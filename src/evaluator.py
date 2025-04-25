"""
Evaluator module for handling LLM queries and evaluating mathematical solutions.
"""

import os
import numpy as np
import google.generativeai as genai
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union
import src.parser as parser
import src.parser_cmt as parser_cmt
from src.parser import ParsingResult
from openai import OpenAI
from collections import Counter
# Get the API key from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found in environment variables")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

# Define supported models
SUPPORTED_MODELS_GEMINI = {
    "Gemini 2.0 Flash Thinking": "gemini-2.0-flash-thinking-exp",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 2.5 Flash Thinking": "gemini-2.5-pro-exp-03-25"
}

SUPPORTED_MODELS_OPENAI = {
    "GPT-4o": "gpt-4o",
    "GPT-4o-mini": "gpt-4o-mini",
    "GPT-o3-mini": "o3-mini",
    "GPT-o1-mini": "o1-mini",
    "GPT-o1": "o1"
}

# Combine the dictionaries using the | operator (Python 3.9+) or dict.update()
SUPPORTED_MODELS = {**SUPPORTED_MODELS_GEMINI, **SUPPORTED_MODELS_OPENAI}

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
    if model_name in SUPPORTED_MODELS_OPENAI:
        return query_openai(input_string, model_name)
    elif model_name in SUPPORTED_MODELS_GEMINI:
        return query_gemini(input_string, model_name)
    else:
        return f"Unsupported model: {model_name}. Supported models: {', '.join(SUPPORTED_MODELS.keys())}", True

def query_openai(input_string: str, model_name: str) -> Tuple[str, bool]:
    model_id = SUPPORTED_MODELS_OPENAI[model_name]
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": input_string}]
        )
        return response.choices[0].message.content, False
    except Exception as e:
        return f"Error querying {model_name}: {str(e)}", True

def query_gemini(input_string: str, model_name: str) -> Tuple[str, bool]:
    model_id = SUPPORTED_MODELS_GEMINI[model_name]
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(f'models/{model_id}')
        response = model.generate_content(input_string,request_options={"timeout": 1000})
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

def evaluate_solution_cmt_numerics(query_string: str, solution_string: str, parameter_string: str, model_name: str) -> EvaluationResult:
    """Evaluate an LLM's solution against a reference solution."""
    print("Entering evaluate_solution_cmt_numerics")
    result = EvaluationResult(model_name=model_name)
    
    # Get model response
    model_response, query_error = query_llm(query_string, model_name)
    if query_error:
        result.error_message = model_response
        return result
    result.model_response = model_response

    # Will come back later
    result.solution_result = None
    result.model_result = None
    
    # Compare evaluation results
    try:
        isequal_=parser_cmt.isequal_numerics(LLM_output=model_response, ground_truth=solution_string)
        result.is_equivalent = isequal_
        result.success = True
        return result
    except Exception as e:
        result.error_message = f"Error comparing evaluation results: {str(e)}"
        return result
    
def compare_latex_expressions(latex_expr_1:str, solution_string:str, parameter_string:str, function_string:str) -> EvaluationResult:
    """Compare two sets of latex expressions using Counters. This hash map comparison relies on the fact that
    the resulting sympy strings must be identical for the two expressions to be equivalent. This is a potential point of failure but results from the fact that Sympy equals does not work for expressions with non-commutative symbols. For now we simply expand all sympy expressions but in the future we should build a more robust set of rewrite rules to ensure equivalent expressions render the same Sympy expression."""

    result = EvaluationResult()
    parsed_expression_1 = parser.solution_to_sympy(latex_expr_1, parameter_string, function_string)
    result.model_result = parsed_expression_1
    parsed_solution = parser.solution_to_sympy(solution_string, parameter_string, function_string)
    result.solution_result = parsed_solution
    parsed_expression_1 = parsed_expression_1.sympy_expressions
    parsed_solution = parsed_solution.sympy_expressions
    # Need to pass error if the expressions do not return a list of len (i.e. they are just None)
    if len(parsed_expression_1) != len(parsed_solution):
        result.error_message = f"Number of expressions do not match: {len(parsed_expression_1)} vs {len(parsed_solution)}"
        result.success = False
        return result
    for i in range(len(parsed_expression_1)):
        parsed_expression_1[i] = parsed_expression_1[i].expand()
        parsed_solution[i] = parsed_solution[i].expand()
    result.success = Counter(parsed_expression_1) == Counter(parsed_solution)
    return result