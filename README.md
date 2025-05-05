# benchmark_eval
Formatting and automatic evaluation of benchmark math problems against LLMs

## Overview
This API provides tools to parse and evaluate mathematical expressions in LaTeX format and compare LLM-generated solutions against reference solutions.

## API Endpoints

### Health Check
```
GET /health
```
Checks if the API service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "latex-parser"
}
```

### Parse LaTeX Expression
```
POST /parse
```
Parses and evaluates a LaTeX mathematical expression.

**Request Body:**
```json
{
  "input": "LaTeX string containing a boxed solution (required)",
  "parameters": "Parameter string, e.g., 'x,y,z' (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "error_message": "",
  "sympy_expressions": ["x**2 + 2*x + 1", "..."],
  "extracted_solutions": ["x^2 + 2x + 1", "..."],
  "intermediate_expressions": ["(x)^(2) + 2*(x) + 1", "..."],
  "parameter_dict": {"x": "Symbol('x')", "...": "..."},
  "evaluation_results": [4.0, "..."]
}
```

If an error occurs during parsing:
```json
{
  "success": false,
  "error_message": "Description of the error",
  "...": null
}
```

### Evaluate LLM Response
```
POST /eval
```
Evaluates an LLM's response against a reference solution.

**Request Body:**
```json
{
  "input": "Prompt sent to the LLM (required)",
  "solution": "Reference solution in LaTeX format (required)",
  "model": "Name of the LLM model (required)",
  "parameters": "Parameter string, e.g., 'x,y,z' (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "error_message": "",
  "model_name": "Gemini 2.0 Flash",
  "model_response": "Full response from the LLM",
  "is_equivalent": true,
  "solution": {
    "success": true,
    "error_message": "",
    "sympy_expressions": ["x**2 + 2*x + 1", "..."],
    "extracted_solutions": ["x^2 + 2x + 1", "..."],
    "intermediate_expressions": ["(x)^(2) + 2*(x) + 1", "..."],
    "parameter_dict": {"x": "Symbol('x')", "...": "..."},
    "evaluation_results": [4.0, "..."]
  },
  "model": {
    "success": true,
    "error_message": "",
    "sympy_expressions": ["x**2 + 2*x + 1", "..."],
    "extracted_solutions": ["x^2 + 2x + 1", "..."],
    "intermediate_expressions": ["(x)^(2) + 2*(x) + 1", "..."],
    "parameter_dict": {"x": "Symbol('x')", "...": "..."},
    "evaluation_results": [4.0, "..."]
  }
}
```

If an error occurs during evaluation:
```json
{
  "success": false,
  "error_message": "Description of the error",
  "model_name": "Gemini 2.0 Flash",
  "model_response": "Full response from the LLM",
  "is_equivalent": false,
  "...": null
}
```

### Query LLM Directly
```
POST /query
```
Sends a prompt to an LLM model and returns the response.

**Request Body:**
```json
{
  "prompt": "Prompt to send to the LLM (required)",
  "model": "Name of the LLM model (required)"
}
```

**Response:**
```json
{
  "success": true,
  "model": "Gemini 2.0 Flash",
  "response": "Response from the LLM"
}
```

If an error occurs:
```json
{
  "success": false,
  "error": "Description of the error"
}
```

### Configuration Management
```
GET /config
```
Gets the current configuration settings (requires admin key in some environments).

**Headers (optional):**
```
X-Admin-Key: your-admin-key
```

**Response:**
```json
{
  "success": true,
  "config": {
    "prompt_suffix": "Current prompt suffix value"
  }
}
```

```
POST /config
```
Updates configuration settings (requires admin key).

**Headers:**
```
X-Admin-Key: your-admin-key
```

**Request Body:**
```json
{
  "prompt_suffix": "New prompt suffix to add to all LLM queries"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully"
}
```

If authentication fails:
```json
{
  "success": false,
  "error": "Unauthorized: Invalid or missing admin key"
}
```

### Render LaTeX
```
POST /render
```
Renders a LaTeX expression to PDF and returns a URL to the file.

**Request Body:**
```json
{
  "latex": "LaTeX string to render (required)"
}
```

**Response:**
```json
{
  "success": true,
  "file_url": "URL to the rendered PDF"
}
```

If an error occurs during rendering:
```json
{
  "error": "Description of the error"
}
```

### List Supported Models
```
GET /models
```
Returns a list of supported LLM models.

**Response:**
```json
{
  "success": true,
  "models": ["Gemini 2.0 Flash Thinking", "Gemini 2.0 Flash", "Gemini 2.5 Flash Thinking"]
}
```

## Special Handling

### Complex Numbers
Complex numbers in evaluation results are returned as strings in Python's complex number format:
- Example: `"(0.7853981633974483-0.6584789484624084j)"`

When comparing results, these strings need to be converted back to complex numbers.

### Parameter Values
By default, when `x` is among the parameters, it is set to the value `2` for evaluation. Other parameters are assigned random values between 1 and 2.

## Environment Variables

- `GEMINI_API_KEY`: API key for Google's Gemini models (required)
- `API_BASE_URL`: Base URL for the API (default: http://localhost:8080)
- `USE_LOCAL_STORAGE`: Whether to use local storage for rendered files (default: false)
- `PORT`: Port to run the API on (default: 8080)
- `ADMIN_KEY`: Key for authenticating admin-only API endpoints (required for production)

## Google Sheets Integration

Two script files are provided for Google Sheets integration:

### benchmark.js
Handles evaluation of mathematical expressions in Google Sheets:
- Checks if LaTeX solutions from different models are equivalent
- Processes rows individually or in batches
- Displays detailed evaluation results

### cmt_benchmark.js
Provides direct LLM querying functionality:
- Sends prompts to LLM models and displays responses
- Manages configuration of the prompt suffix
- Supports admin-only configuration functions

## Setting Up Google Sheets Integration

1. Open your Google Sheet
2. Go to Extensions > Apps Script
3. Copy the content of either `benchmark.js` or `cmt_benchmark.js` into the editor
4. Save and reload your sheet
5. Use the custom menu to:
   - Configure the API URL (admin only)
   - Set the admin key (admin only)
   - Configure column mappings (admin only)
   - Query LLMs or evaluate solutions

## Running the API

```bash
# Start the API
python api.py

# Run with development mode for auto-reloading
export FLASK_ENV=development
export FLASK_APP=api.py
python -m flask run
```
