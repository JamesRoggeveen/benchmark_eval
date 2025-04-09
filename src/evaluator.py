"""
Evaluator module for handling LLM queries and evaluating mathematical solutions.
"""

import os
import numpy as np
import google.generativeai as genai
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union
import src.parser as parser
from src.parser import ParsingResult

# Get the API key from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found in environment variables")

# Define supported models
SUPPORTED_MODELS = {
    "Gemini 2.0 Flash Thinking": "gemini-2.0-flash-thinking-exp",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 2.5 Flash Thinking": "gemini-2.5-pro-exp-03-25"
}

@dataclass
class EvaluationResult:
    """Container for evaluation results"""
    success: bool = False
    error_message: str = ""
    model_name: str = ""
    model_response: Optional[str] = None
    solution_result: Optional[ParsingResult] = None
    model_result: Optional[ParsingResult] = None
    is_equivalent: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the evaluation result to a dictionary for JSON serialization"""
        result = {
            "success": self.success,
            "error_message": self.error_message,
            "model_name": self.model_name,
            "model_response": self.model_response,
            "is_equivalent": self.is_equivalent
        }
        
        # Add solution result if available
        if self.solution_result:
            result["solution"] = self.solution_result.to_dict()
            
        # Add model result if available
        if self.model_result:
            result["model"] = self.model_result.to_dict()
            
        return result

def query_llm(input_string: str, model_name: str) -> Tuple[str, bool]:
    """Query an LLM with the given input string."""
    if model_name not in SUPPORTED_MODELS:
        return f"Unsupported model: {model_name}. Supported models: {', '.join(SUPPORTED_MODELS.keys())}", True
    
    model_id = SUPPORTED_MODELS[model_name]
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(f'models/{model_id}')
        response = model.generate_content(input_string)
        return response.text, False
    except Exception as e:
        return f"Error querying {model_name}: {str(e)}", True

def evaluate_solution(query_string: str, solution_string: str, parameter_string: str, model_name: str) -> EvaluationResult:
    """Evaluate an LLM's solution against a reference solution."""
    result = EvaluationResult(model_name=model_name)
    
    # Process reference solution
    solution_result = parser.evaluate_solution(solution_string, parameter_string)
    if not solution_result.success or not solution_result.evaluation_results:
        result.error_message = f"Failed to evaluate reference solution: {solution_result.error_message}"
        return result
    
    result.solution_result = solution_result
    
    # Get model response
    model_response, query_error = query_llm(query_string, model_name)
    if query_error:
        result.error_message = model_response
        return result
    
    result.model_response = model_response
    
    # Process model response
    model_result = parser.evaluate_solution(model_response, parameter_string)
    if not model_result.success or not model_result.evaluation_results:
        result.error_message = f"Failed to evaluate model response: {model_result.error_message}"
        return result
    
    result.model_result = model_result
    
    # Compare evaluation results
    try:
        solution_array = np.array(solution_result.evaluation_results, dtype=np.float64)
        model_array = np.array(model_result.evaluation_results, dtype=np.float64)
        
        # Check if shape of arrays match
        if solution_array.shape != model_array.shape:
            result.error_message = f"Evaluation shapes don't match: {solution_array.shape} vs {model_array.shape}"
            return result
        
        result.is_equivalent = np.allclose(model_array, solution_array, atol=1e-6)
        result.success = True
        return result
    except Exception as e:
        result.error_message = f"Error comparing evaluation results: {str(e)}"
        return result
