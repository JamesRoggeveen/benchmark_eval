# Load environment variables from .env file - ONLY IN DEVELOPMENT
import os

# Only load from .env if we're not in production mode
if os.environ.get('ENV', 'development').lower() != 'production':
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Development mode: Loaded environment from .env file")
    except ImportError:
        print("Warning: python-dotenv not installed, skipping .env loading")

from flask import Flask, request, jsonify, send_from_directory
from src.latex_render import render_latex, LatexError
from src.storage import get_storage_backend
import src.parser as parser
from src.evaluator import evaluate_solution, evaluate_numeric_solution, evaluate_functional_solution, SUPPORTED_MODELS, query_llm, evaluate_solution_cmt_numerics

app = Flask(__name__)

# Initialize storage backend
storage_client = get_storage_backend()

# Global configuration dictionary for server settings, default is empty string
CONFIG = {
    "prompt_suffix": ""
}

# Configure local file serving if using local storage
if os.environ.get('USE_LOCAL_STORAGE', 'false').lower() == 'true':
    app.config['LOCAL_STORAGE_PATH'] = os.path.join(os.getcwd(), 'local_storage')
    
    @app.route('/files/<path:filename>')
    def serve_file(filename):
        return send_from_directory(app.config['LOCAL_STORAGE_PATH'], filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "latex-parser"})

def check_field(data, key):
    """Check if a field exists in the request data and is valid"""
    print(f"Checking field '{key}': {data.get(key, 'NOT FOUND')}")  # Debug log
    
    if key not in data:
        print(f"Missing field '{key}' in request data")  # Debug log
        return f"Missing '{key}' field in JSON", 400
    
    if not isinstance(data[key], str):
        print(f"Field '{key}' is not a string, got type: {type(data[key])}")  # Debug log
        return f"{key} must be a string", 400
    
    if not data[key].strip():
        print(f"Field '{key}' is empty or only whitespace")  # Debug log
        return f"{key} string is empty", 400
    
    return None, 200  # Return None for error and 200 for status when check passes

@app.route('/parse', methods=['POST'])
def parse_endpoint():
    """Parse and evaluate a LaTeX solution string"""
    try:
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({"error": "Missing input field", "success": False}), 400
            
        input_string = data['input']
        parameter_str = data.get('parameters', '')
        
        result = parser.evaluate_solution(input_string, parameter_str)
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500
    
@app.route('/parse_cmt', methods=['POST'])
def parse_cmt_endpoint():
    """Parse and evaluate a CMT solution string"""
    try:
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({"error": "Missing input field", "success": False}), 400
            
        input_string = data['input']
        parameter_str = data.get('parameters', '')
        function_str = data.get('functions', '')
        
        try:
            if parameter_str=='' and function_str=='':
                numeric_parse_attempt = parser.parse_numeric_solution(input_string)
                if numeric_parse_attempt.success:
                    result = numeric_parse_attempt
                else:
                    result = parser.evaluate_solution(input_string, parameter_str)
            elif parameter_str!='' and function_str=='' and 'NC' not in parameter_str:
                result = parser.evaluate_solution(input_string, parameter_str)
            else:
                result = parser.solution_to_sympy(input_string, parameter_str, function_str)

            return jsonify(result.to_dict())

        except Exception as parser_error:
            error_msg = f"Parser error: {str(parser_error)}"
            print(f"Error in parse_cmt: {error_msg}")  # Debug log
            return jsonify({
                "error": error_msg,
                "success": False,
                "error_type": "parser_error",
                "error_details": {
                    "input": data['input'],
                    "parameters": parameter_str,
                    "functions": function_str
                }
            }), 500

    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"Error in parse_cmt: {error_msg}")  # Debug log
        return jsonify({
            "error": error_msg,
            "success": False,
            "error_type": "server_error",
            "error_details": {
                "request_data": str(request.get_json()) if request.is_json else "No JSON data"
            }
        }), 500
    

@app.route('/config', methods=['GET', 'POST'])
def config_endpoint():
    """Get or update server configuration"""
    # Only allow admin access to this endpoint in production
    if os.environ.get('ENV', 'development').lower() == 'production':
        # In a real app, you would add proper authentication here
        admin_key = request.headers.get('X-Admin-Key')
        if not admin_key or admin_key != os.environ.get('ADMIN_KEY', ''):
            return jsonify({"error": "Unauthorized", "success": False}), 401
    
    if request.method == 'GET':
        # Return the current configuration
        return jsonify({
            "success": True,
            "config": CONFIG
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided", "success": False}), 400
            
            # Update prompt suffix if provided
            if 'prompt_suffix' in data:
                if not isinstance(data['prompt_suffix'], str):
                    return jsonify({"error": "prompt_suffix must be a string", "success": False}), 400
                CONFIG['prompt_suffix'] = data['prompt_suffix']
            
            return jsonify({
                "success": True,
                "message": "Configuration updated successfully",
                "config": CONFIG
            })
        except Exception as e:
            return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500

@app.route('/query', methods=['POST'])
def query_endpoint():
    """Query an LLM with a prompt and return the response"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "success": False}), 400
            
        # Validate required fields
        for key in ['prompt', 'model']:
            error, status_code = check_field(data, key)
            if error:
                return jsonify({"error": error, "success": False}), status_code
        
        # Append configured prompt suffix to the user's prompt
        prompt = data['prompt'] + CONFIG['prompt_suffix']
        
        # Query the model
        response, is_error = query_llm(prompt, data['model'])
        
        if is_error:
            return jsonify({
                "success": False,
                "prompt": prompt,
                "error": response,
                "model": data['model']
            }), 400
        
        # Return successful response
        return jsonify({
            "success": True,
            "prompt": prompt,
            "response": response,
            "model": data['model']
        })
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500

@app.route('/eval', methods=['POST'])
def eval_endpoint():
    """Evaluate an LLM's answer against a reference solution"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "success": False}), 400
            
        # Validate required fields
        for key in ['input', 'solution', 'model']:
            error, status_code = check_field(data, key)
            if error:
                return jsonify({"error": error, "success": False}), status_code
        
        # Get parameters with default empty string
        parameter_str = data.get('parameters', '')

        # Replace commas with semicolons in parameter string for backwards compatibility
        parameter_str = parameter_str.replace(',', ';')
        
        # Evaluate the solution
        result = evaluate_solution(query_string=data['input'], solution_string=data['solution'], parameter_string=parameter_str, model_name=data['model'])
        
        # Convert the result to a dictionary and return
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500

@app.route('/eval_cmt_numerics', methods=['POST'])
def eval_cmt_numerics_endpoint():
    """Evaluate an LLM's answer against a reference solution"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "success": False}), 400
            
        # Validate required fields
        for key in ['input', 'solution', 'model']:
            error, status_code = check_field(data, key)
            if error:
                return jsonify({"error": error, "success": False}), status_code
        
        # Get parameters with default empty string
        parameter_str = data.get('parameters', '')
        
        # Evaluate the solution
        result = evaluate_solution_cmt_numerics(query_string=data['input'], solution_string=data['solution'], parameter_string=parameter_str, model_name=data['model'])
        print('print: result')
        print(result)
        
        # Convert the result to a dictionary and return
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500
    
@app.route('/eval_cmt', methods=['POST'])
def eval_cmt_endpoint():
    """Evaluate an LLM's answer against a reference solution"""
    try:
        data = request.get_json()
        if not data:
            print("No JSON data in request")  # Debug log
            return jsonify({"error": "No JSON data provided", "success": False}), 400
        
        print(f"Received request data: {data}")  # Debug log
        
        for key in ['input', 'solution', 'model']:
            error, status_code = check_field(data, key)
            if error:
                print(f"Field validation failed for '{key}': {error}")  # Debug log
                return jsonify({"error": error, "success": False}), status_code
            
        parameter_str = data.get('parameters', '')
        function_str = data.get('functions', '')

        try:
            if parameter_str=='' and function_str=='':
                numeric_parse_attempt = parser.parse_numeric_solution(data['solution'])
                if numeric_parse_attempt.success:
                    result = evaluate_numeric_solution(query_string=data['input'], solution_string=data['solution'], model_name=data['model'])
                else:
                    result = evaluate_solution(query_string=data['input'], solution_string=data['solution'], parameter_string=parameter_str, model_name=data['model'])
            elif parameter_str!='' and function_str=='' and 'NC' not in parameter_str:
                result = evaluate_solution(query_string=data['input'], solution_string=data['solution'], parameter_string=parameter_str, model_name=data['model'])
            else:
                result = evaluate_functional_solution(query_string=data['input'], solution_string=data['solution'], parameter_string=parameter_str, function_string=function_str, model_name=data['model'])

            return jsonify(result.to_dict())

        except Exception as eval_error:
            error_msg = f"Evaluation error: {str(eval_error)}"
            print(f"Error in eval_cmt: {error_msg}")  # Debug log
            return jsonify({
                "error": error_msg,
                "success": False,
                "error_type": "evaluation_error",
                "error_details": {
                    "input": data['input'],
                    "solution": data['solution'],
                    "model": data['model'],
                    "parameters": parameter_str,
                    "functions": function_str
                }
            }), 500

    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"Error in eval_cmt: {error_msg}")  # Debug log
        return jsonify({
            "error": error_msg,
            "success": False,
            "error_type": "server_error",
            "error_details": {
                "request_data": str(request.get_json()) if request.is_json else "No JSON data"
            }
        }), 500

@app.route('/render', methods=['POST'])
def render_endpoint():
    """API endpoint for rendering LaTeX"""
    try:
        data = request.get_json()
        if not data or 'latex' not in data:
            return jsonify({'error': 'No LaTeX content provided'}), 400
        
        latex_string = data['latex']
        output_dir = os.path.join(os.getcwd(), 'output')
        pdf_path = render_latex(latex_string, output_dir)
        
        try:
            # Upload using configured storage backend
            # Storage backend handles cleanup of source files
            public_url = storage_client.upload_file(pdf_path)
            
            return jsonify({
                'success': True,
                'file_url': public_url
            })
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    except LatexError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """Return a list of supported LLM models"""
    return jsonify({
        "success": True,
        "models": list(SUPPORTED_MODELS.keys())
    })

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8080))
    
    print(f"Storage mode: {'local' if os.environ.get('USE_LOCAL_STORAGE', 'false').lower() == 'true' else 'cloud'}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port) 