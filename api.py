import os
from flask import Flask, request, jsonify, send_from_directory
from src.latex_render import render_latex, LatexError
from src.storage import get_storage_backend
import src.parser as parser
import os
import google.generativeai as genai
import numpy as np
import sympy as sp

# Load environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()

app = Flask(__name__)

# Initialize storage backend
storage_client = get_storage_backend()

# Configure local file serving if using local storage
if os.environ.get('USE_LOCAL_STORAGE', 'false').lower() == 'true':
    app.config['LOCAL_STORAGE_PATH'] = os.path.join(os.getcwd(), 'local_storage')
    
    @app.route('/files/<path:filename>')
    def serve_file(filename):
        return send_from_directory(app.config['LOCAL_STORAGE_PATH'], filename)

# Get the API key from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found in environment variables")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "latex-parser"})

def my_parse_function(input_string):
    output = {"parsed": False,
              "error": "",
              "solution_latex": None,
              "solution_expr": None,
              "solution_eval": None}
    if not input_string:
        output["error"] = "No input provided"
        return output
    
    try:
        extracted_solution = parser.extract_solution(input_string)
        output["solution_latex"] = extracted_solution
    except Exception as e:
        output["error"] = f"Could not extract solution from input: {str(e)}"
        return output
        
    expr_list = [parser.latex_to_expression(s) for s in extracted_solution]
    output["solution_expr"] = expr_list
    try:
        sympy_solution_list = [parser.expression_to_sympy(expr) for expr in expr_list]
    except Exception as e:
        output["error"] = f"Could not parse expression: {str(e)}"
        return output
    try:
        evaluated_solution = [float(parser.evaluate_sympy_solution(sympy_solution, 2)) for sympy_solution in sympy_solution_list]
        output["solution_eval"] = evaluated_solution
        output["parsed"] = True
        return output
    except Exception as e:
        output["error"] = f"Error evaluating expression: {str(e)}"
        return output
    
def my_query_function(input_string):
    output = {"parsed": False,
              "error": "",
              "solution_latex": None,
              "solution_expr": None,
              "solution_eval": None,
              "query_response": None}
    genai.configure(api_key=GEMINI_API_KEY)
    Gemini_Model = genai.GenerativeModel('models/gemini-2.0-flash-thinking-exp')
    try:
        response = Gemini_Model.generate_content(input_string)
        output["query_response"] = response.text
        parse_output = my_parse_function(response.text)
        for key, value in parse_output.items():
            output[key] = value
        return output
    except Exception as e:
        output["error"] = f"Error querying Gemini: {str(e)}"
        return output
    
def my_eval_function(input_string,solution_string):
    output = {"error": "",
              "solution_parsed": False,
              "error": "",
              "solution_latex": None,
              "solution_expr": None,
              "solution_eval": None,
              "model_parsed":False,
              "model_latex": None,
              "model_error": "",
              "model_expr": None,
              "model_eval": None,
              "eval_error": "",
              "eval_equivalent": False,
              "query_response": None}
    try:
        query_output = my_query_function(input_string)
        output["query_response"] = query_output["query_response"]
        output["model_latex"] = query_output["solution_latex"]
        output["model_expr"] = query_output["solution_expr"]
        output["model_eval"] = query_output["solution_eval"]
        output["model_parsed"] = query_output["parsed"]
        
        solution_output = my_parse_function(solution_string)
        for key, value in solution_output.items():
            output[key] = value
        model_eval = np.array(output["model_eval"])
        solution_eval = np.array(output["solution_eval"])
        if model_eval.shape != solution_eval.shape:
            output["eval_error"] = "Model and solution eval arrays have different shapes"
            return output
        if np.allclose(model_eval, solution_eval, atol=1e-6):
            output["eval_equivalent"] = True
        else:
            output["eval_equivalent"] = False
        return output
    except Exception as e:
        output["error"] = f"Error evaluating model: {str(e)}"
        return output
    
def query_gemini_model(input_string, model):
    genai.configure(api_key=GEMINI_API_KEY)
    Gemini_Model = genai.GenerativeModel('models/'+model)
    try:
        response = Gemini_Model.generate_content(input_string)
        return response.text, False
    except Exception as e:
        return f"Error querying {model}: {str(e)}", True
    
def eval_solution_with_parameters(input_string, solution_string, parameter_string, model):
    output = {"model": model,
              "eval_result": False,
              "error_messages": "",
              "solution_expr_list": None,
              "model_expr_list": None,
              "solution_values": None,
              "model_values": None,
              "model_response": None}
    
    # Helper function to process parsed values and convert to JSON-serializable floats
    def process_values(values, expr_list, value_type="solution"):
        try:
            float_values = []
            for val in values:
                try:
                    float_val = complex(val).real if isinstance(val, sp.Basic) else float(val)
                    float_values.append(float_val)
                except Exception as e:
                    return None, f"Error converting {value_type} value {val}: {str(e)}"
            
            # Convert expressions to strings for JSON serialization
            expr_strings = [str(expr) for expr in expr_list] if expr_list else None
            return float_values, expr_strings, None
        except Exception as e:
            return None, None, f"Error processing {value_type} values: {str(e)}"
    
    # Process solution
    solution_values, parse_error_message, solution_expr_list = parser.evaluate_solution_with_parameters(solution_string, parameter_string)
    if parse_error_message != "" or solution_values is None:
        output["error_messages"] = f"Failed to evaluate solution: {parse_error_message}"
        return output
    
    # Process solution values
    solution_float_values, solution_expr_str_list, solution_error = process_values(solution_values, solution_expr_list, "solution")
    if solution_error:
        output["error_messages"] = solution_error
        return output
    else:
        output["solution_values"] = solution_float_values
        output["solution_expr_list"] = solution_expr_str_list
    
    # Get model response
    query_response, query_error = query_gemini_model(input_string, model)
    if query_error:
        output["error_messages"] = query_response
        return output
    output["model_response"] = query_response
    
    # Process model
    model_values, model_error_message, model_expr_list = parser.evaluate_solution_with_parameters(query_response, parameter_string)
    if model_error_message != "" or model_values is None:
        output["error_messages"] = f"Failed to evaluate model response: {model_error_message}"
        return output
    
    # Process model values
    model_float_values, model_expr_str_list, model_error = process_values(model_values, model_expr_list, "model")
    if model_error:
        output["error_messages"] = model_error
        return output
    
    # Store model results
    output["model_values"] = model_float_values
    output["model_expr_list"] = model_expr_str_list
    
    # Compare arrays
    try:
        solution_array = np.array(solution_float_values, dtype=np.float64)
        model_array = np.array(model_float_values, dtype=np.float64)
        output["eval_result"] = np.allclose(model_array, solution_array, atol=1e-6)
    except Exception as e:
        output["error_messages"] = f"Error comparing values: {str(e)}"
        
    return output

def check_field(data, key):
    if key not in data:
        return f"Missing '{key}' field in JSON", 400
    if not isinstance(data[key], str):
        return f"{key} must be a string", 400
    if not data[key].strip():
        return f"{key} string is empty", 400
    return None, 200  # Return None for error and 200 for status when check passes

@app.route('/eval_model', methods=['POST'])
def eval_model():
    output = {"model": None,
              "eval_result": False,
              "error_messages": "",
              "solution_expr_list": None,
              "model_expr_list": None,
              "solution_values": None,
              "model_values": None,
              "model_response": None}
    model_list = {"Gemini 2.0 Flash Thinking": "gemini-2.0-flash-thinking-exp","Gemini 2.0 Flash": "gemini-2.0-flash","Gemini 2.5 Flash Thinking": "gemini-2.5-pro-exp-03-25"}
    try:
        data = request.get_json()
        if not data:
            output["error_messages"] = "No JSON data provided"
            return jsonify(output), 400
        for key in ['input','solution','parameters','model']:
            error, status_code = check_field(data,key)
            if error:
                output["error_messages"] = error
                return jsonify(output), status_code
        input_string = data['input']
        solution_string = data['solution']
        parameter_string = data['parameters']
        model_name = data['model']
        if model_name not in model_list:
            output["error_messages"] = f"Invalid model name. Must be one of: {', '.join(model_list.keys())}"
            return jsonify(output), 400
        model = model_list[model_name]
        output = eval_solution_with_parameters(input_string, solution_string, parameter_string, model)
        return jsonify(output)
    except Exception as e:
        output["error_messages"] = f"Server error: {str(e)}"
        return jsonify(output), 500

@app.route('/parse', methods=['POST'])
def parse():
    output = {"parsed": False,
              "error": "",
              "solution_latex": None,
              "solution_expr": None,
              "solution_eval": None}
    try:
        data = request.get_json()
        if not data or 'input' not in data:
            output["error"] = "Missing input field"
            return jsonify(output), 400
            
        input_string = data['input']
        result = my_parse_function(input_string)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "parsed": False}), 500
    
@app.route('/query', methods=['POST'])
def query():
    output = {"parsed": False,
              "error": "",
              "solution_latex": None,
              "solution_expr": None,
              "solution_eval": None}
    try:
        data = request.get_json()
        if not data:
            output["error"] = "No JSON data provided"
            return jsonify(output), 400
        error, status_code = check_field(data,'input')
        if error:
            return jsonify({"error": error}), status_code
        
        input_string = data['input']
        result = my_query_function(input_string)
        return jsonify(result)
    except Exception as e:
        output["error"] = f"Server error: {str(e)}"
        return jsonify(output), 500
    
@app.route('/eval', methods=['POST'])
def eval():
    output = {"error": "",
              "solution_parsed": False,
              "error": "",
              "solution_latex": None,
              "solution_expr": None,
              "solution_eval": None,
              "model_parsed":False,
              "model_latex": None,
              "model_error": "",
              "model_expr": None,
              "model_eval": None,
              "eval_error": "",
              "eval_equivalent": False,
              "query_response": None}
    try:
        data = request.get_json()
        if not data:
            output["error"] = "No JSON data provided"
            return jsonify(output), 400
        for key in ['input','solution']:
            error, status_code = check_field(data,key)
            if error:
                return jsonify({"error": error}), status_code
        
        input_string = data['input']
        solution_string = data['solution']
        result = my_eval_function(input_string,solution_string)
        return jsonify(result)
    except Exception as e:
        output["error"] = f"Server error: {str(e)}"
        return jsonify(output), 500

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

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8080))
    
    print(f"Storage mode: {'local' if os.environ.get('USE_LOCAL_STORAGE', 'false').lower() == 'true' else 'cloud'}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port) 