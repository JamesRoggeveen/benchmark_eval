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
from src.evaluator import evaluate_solution, SUPPORTED_MODELS

app = Flask(__name__)

# Initialize storage backend
storage_client = get_storage_backend()

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
    if key not in data:
        return f"Missing '{key}' field in JSON", 400
    if not isinstance(data[key], str):
        return f"{key} must be a string", 400
    if not data[key].strip():
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
        
        # Evaluate the solution
        result = evaluate_solution(query_string=data['input'], solution_string=data['solution'], parameter_string=parameter_str, model_name=data['model'])
        
        # Convert the result to a dictionary and return
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500

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