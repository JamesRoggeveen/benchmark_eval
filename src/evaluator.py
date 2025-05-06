"""
Evaluator module for handling LLM queries and evaluating mathematical solutions.
"""

import os
import numpy as np
import google.generativeai as genai
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import src.parser as parser
import src.parser_cmt as parser_cmt
import src.parser_lark as parser_lark
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
    "Gemini 2.5 Flash Thinking": "gemini-2.5-pro-exp-03-25",
    "Gemini 2.5 Pro Preview": "gemini-2.5-pro-preview-03-25"
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

def evaluate_model(query_string: str, solution_string: str, parameter_string: str, function_str: str, model_name: str, parse_function: Callable, eval_function: Callable) -> EvaluationResult:
    """Evaluate an LLM's solution against a reference solution."""
    result = EvaluationResult(model_name=model_name)
    
    # Process reference solution
    solution_result = parse_function(solution_string, parameter_string, function_str)
    if not solution_result.success:
        result.error_message = f"Failed to parse reference solution: {solution_result.error_message}"
        return result

    result.solution_result = solution_result
    
    # Get model response
    model_response, query_error = query_llm(query_string, model_name)
    if query_error:
        result.error_message = model_response
        return result
    
    result.model_response = model_response
    
    # Process model response
    model_result = parse_function(model_response, parameter_string, function_str)
    if not model_result.success:
        result.error_message = f"Failed to parse model response: {model_result.error_message}"
        return result
    
    result.model_result = model_result
    
    # Compare evaluation results
    return eval_function(result)

def evaluate_solution(query_string: str, solution_string: str, parameter_string: str, model_name: str) -> EvaluationResult:
    print("Entering evaluate_solution")
    return evaluate_model(query_string, solution_string, parameter_string, "", model_name, parser.evaluate_solution, is_equivalent_numerics)

def evaluate_numeric_solution(query_string: str, solution_string: str, model_name: str) -> EvaluationResult:
    print("Entering evaluate_numeric_solution")
    return evaluate_model(query_string, solution_string, "", "", model_name, parser.parse_numeric_solution, is_equivalent_numerics)

def evaluate_functional_solution(query_string: str, solution_string: str, parameter_string: str, function_string: str, model_name: str) -> EvaluationResult:
    print("Entering evaluate_functional_solution")
    return evaluate_model(query_string, solution_string, parameter_string, function_string, model_name, parser.solution_to_sympy, is_equivalent_functional_form)

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

    # TODO: Will come back later
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

def evaluate_solution_cmt_symbolics(query_string: str, solution_string: str, parameter_string: str, model_name: str) -> EvaluationResult:
    """Evaluate an LLM's solution against a reference solution."""
    print("Entering evaluate_solution_cmt_symbolics")
    result = EvaluationResult(model_name=model_name)
    
    # Get model response
    model_response, query_error = query_llm(query_string, model_name)
    if query_error:
        result.error_message = model_response
        return result
    result.model_response = model_response

    # TODO: Will come back later
    result.solution_result = None
    result.model_result = None
    
    # Compare evaluation results
    try:
        isequal_=parser_lark.isequal_symbolics(LLM_output=model_response, ground_truth=solution_string, noncomm_str = parameter_string)
        result.is_equivalent = isequal_
        result.success = True
        return result
    except Exception as e:
        result.error_message = f"Error comparing evaluation results: {str(e)}"
    
def is_equivalent_functional_form(result: EvaluationResult) -> EvaluationResult:
    """Compare two sets of latex expressions using Counters. This hash map comparison relies on the fact that
    the resulting sympy strings must be identical for the two expressions to be equivalent. This is a potential point of failure but results from the fact that Sympy equals does not work for expressions with non-commutative symbols. For now we simply expand all sympy expressions but in the future we should build a more robust set of rewrite rules to ensure equivalent expressions render the same Sympy expression."""

    try:
        # Get sympy expressions
        model_exprs = result.model_result.sympy_expressions
        solution_exprs = result.solution_result.sympy_expressions
        local_dict = {**result.solution_result.parameter_dict, **result.solution_result.function_dict}
        
        # Validate expressions exist
        if not model_exprs or not solution_exprs:
            result.error_message = "One or both expressions failed to parse to SymPy expressions"
            result.success = False
            return result
            
        # Check expression counts match
        if len(model_exprs) != len(solution_exprs):
            result.error_message = f"Number of expressions do not match: {len(model_exprs)} vs {len(solution_exprs)}"
            result.success = True
            return result
    

        try:
            n = len(model_exprs)
            expression_difference = []
            if any('_dagger' in key for key in local_dict.keys()):
                fermionic_flag = True
            else:
                fermionic_flag = False
            results = np.zeros((n,n))
            for i,expr1 in enumerate(model_exprs):
                for j,expr2 in enumerate(solution_exprs):
                    diff = (expr1 - expr2).doit()
                    if fermionic_flag:
                        diff = parser.simplify_fermionic_expression(diff, local_dict)
                    expression_difference.append(diff)
                    results[i,j] = (diff.simplify() == 0)
            result.is_equivalent = all(any(row) for row in results)
        # try:
        #     model_exprs = [expr.expand() for expr in model_exprs]
        #     solution_exprs = [expr.expand() for expr in solution_exprs]
        except Exception as e:
            result.error_message = f"Error expanding expressions: {str(e)}"
            result.success = False
            return result
            
        # Compare expressions using Counter
        # result.is_equivalent = Counter(model_exprs) == Counter(solution_exprs)
        result.success = True
        return result
        
    except Exception as e:
        result.error_message = f"Unexpected error during comparison: {str(e)}"
        return result
    
def is_equivalent_numerics(result: EvaluationResult)->EvaluationResult:
    try:
        # Custom sort key that handles both complex and float values
        def sort_key(x):
            if hasattr(x, '__getitem__'):
                val = x[0]
            else:
                val = x
            # For complex numbers, sort by real part then imaginary part
            if isinstance(val, complex):
                return (val.real, val.imag)
            return (float(val), 0)  # Convert to float and use 0 for imaginary part
            
        model_solution = sorted(result.model_result.evaluation_results, key=sort_key)
        solution_solution = sorted(result.solution_result.evaluation_results, key=sort_key)
        
        # Check if shape of arrays match
        if len(model_solution) != len(solution_solution):
            result.error_message = f"Evaluation shapes don't match: {len(solution_solution)} vs {len(model_solution)}"
            result.success = True
            result.is_equivalent = False
            return result
        equivalent = True

        for model_element, solution_element in zip(model_solution, solution_solution):
            # Check if both are tuples/lists or both are scalar values
            if hasattr(model_element, '__len__') != hasattr(solution_element, '__len__'):
                # One is tuple/list and other is scalar
                result.error_message = f"Mismatched types: one is tuple/list and other is scalar"
                result.success = True
                result.is_equivalent = False
                return result
            elif hasattr(model_element, '__len__'):
                # Both are tuples/lists, check lengths match
                if len(model_element) != len(solution_element):
                    result.error_message = f"Evaluation shapes don't match: {len(solution_element)} vs {len(model_element)}"
                    result.success = True
                    result.is_equivalent = False
                    return result
            equivalent *= np.allclose(model_element, solution_element, atol=1e-6)
        result.is_equivalent = bool(equivalent)
        result.success = True
        return result
    except Exception as e:
        result.error_message = f"Error comparing evaluation results: {str(e)}"
