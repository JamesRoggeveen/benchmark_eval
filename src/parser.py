import sympy as sp
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application, convert_xor, implicit_application
import regex as re
import numpy as np
import argparse
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from src.parser_rules import deletion_rules, replacement_rules, function_rules, nested_rules, final_rules, known_functions

class ParseError(Exception):
    """Base class for all parsing related errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error

    def __str__(self) -> str:
        return self.message

class SolutionExtractionError(ParseError):
    """Raised when unable to extract solution from boxed environment"""
    pass

class LatexConversionError(ParseError):
    """Raised when unable to convert LaTeX to a standard expression"""
    def __init__(self, message: str, latex: str, rule: Optional[str] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.latex = latex
        self.rule = rule

class SymPyConversionError(ParseError):
    """Raised when unable to convert expression to SymPy"""
    def __init__(self, message: str, expression: str, stage: str, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.expression = expression
        self.stage = stage

class EvaluationError(ParseError):
    """Raised when unable to evaluate a SymPy expression"""
    def __init__(self, message: str, expression: Any, parameters: Optional[Dict] = None,
                 original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
        self.expression = expression
        self.parameters = parameters

# ===== Data Structures =====
@dataclass
class ParsingResult:
    """Container for parsing results to avoid excessive tuple returns"""
    sympy_expressions: Optional[List[sp.Expr]] = None
    error_message: str = ""
    extracted_solutions: Optional[List[str]] = None
    intermediate_expressions: Optional[List[str]] = None
    parameter_dict: Optional[Dict[sp.Symbol, Any]] = None
    evaluation_results: Optional[List[Any]] = None
    
    @property
    def success(self) -> bool:
        """Check if parsing was successful"""
        return self.error_message == ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the ParsingResult to a JSON-serializable dictionary."""
        # First convert to a dictionary using dataclasses.asdict
        result_dict = asdict(self)
        
        # Add success property
        result_dict['success'] = self.success
        
        # Handle sympy expressions (convert to strings)
        if result_dict['sympy_expressions']:
            result_dict['sympy_expressions'] = [str(expr) for expr in result_dict['sympy_expressions']]
        
        # Handle sympy symbols in parameter_dict
        if result_dict['parameter_dict']:
            param_dict = {}
            for key, value in result_dict['parameter_dict'].items():
                # Convert sympy symbols to strings
                if isinstance(key, sp.Symbol):
                    key = str(key)
                param_dict[key] = str(value)
            result_dict['parameter_dict'] = param_dict
        
        # Handle complex numbers in evaluation_results
        if result_dict['evaluation_results']:
            serialized_results = []
            for value in result_dict['evaluation_results']:
                if isinstance(value, complex):
                    # Format complex numbers in a standard form
                    serialized_results.append(str(value))
                else:
                    serialized_results.append(value)
            result_dict['evaluation_results'] = serialized_results
            
        return result_dict

# ===== Main Parsing Functions =====
def extract_solution(solution_string: str) -> List[str]:
    """Extract solution from boxed environment in LaTeX string"""
    if not solution_string or not solution_string.strip():
        raise SolutionExtractionError("Empty solution string provided")
        
    try:
        # boxed search string from matharena
        solution_group = re.search(r"(boxed|fbox)\{((?:[^\{}\}]|\{(?2)\})*)\}", solution_string)
        if not solution_group:
            raise SolutionExtractionError("No boxed solution found in response")
        
        solution = solution_group.group(2)
        if not solution.strip():
            raise SolutionExtractionError("Empty solution found in boxed environment")
            
        solution_list = solution.split(';')
        solution_list = [s.strip() for s in solution_list]
        
        # Validate each solution part
        for i, part in enumerate(solution_list):
            if not part:
                raise SolutionExtractionError(f"Empty solution part found at index {i}")
                
        return solution_list
    
    except re.error as e:
        raise SolutionExtractionError(f"Regex error while extracting solution: {str(e)}", e)
    except SolutionExtractionError:
        raise
    except Exception as e:
        raise SolutionExtractionError(f"Unexpected error while extracting solution: {str(e)}", e)

def latex_to_expression(latex_string: str) -> str:
    """Convert LaTeX string to an expression suitable for SymPy parsing"""
    if not latex_string or not latex_string.strip():
        raise LatexConversionError("Empty LaTeX string provided", latex_string)
        
    try:
        current_string = latex_string
        
        # Apply deletion rules
        for pattern in deletion_rules:
            current_string = re.sub(pattern, "", current_string)
        
        # Apply function rules
        for pattern, replacement in function_rules.items():
            current_string = re.sub(pattern, replacement, current_string)
        
        # Apply nested rules iteratively until no more changes
        for _ in range(5):  # Limit iterations to prevent infinite loops
            init_string = current_string
            for pattern, replacement in nested_rules.items():
                current_string = re.sub(pattern, replacement, current_string)
            if current_string == init_string:
                break
        
        # Apply final rules, which consist of one time rules that would mess up nested logic
        for pattern, replacement in final_rules.items():
            current_string = re.sub(pattern, replacement, current_string)
        
        # Add additional space before known functions to prevent them from being parsed as variables (i.e. x\ln(x) -> x \ln(x))
        for function in known_functions:
            # Add space before function if preceded by non-space
            current_string = re.sub(fr'(?<=[^\s])(\\{function})', r' \1', current_string)
        
        # Find known functions that are using implicit application to add parentheses, i.e \sin \theta -> \sin(\theta)
        function_pattern = fr'\\({"|".join(known_functions)})\s*([^{{}}\s()+\-*\/^]+)'
        current_string = re.sub(function_pattern, r' \1(\2)', current_string)

        # Apply replacement rules
        for pattern, replacement in replacement_rules.items():
            current_string = re.sub(pattern, replacement, current_string)
        
        # Remove remaining backslashes
        current_string = re.sub(r'\\', '', current_string)
        
        # Final validation
        if not current_string.strip():
            raise LatexConversionError("Conversion resulted in empty string", latex_string)
            
        return current_string
        
    except LatexConversionError:
        raise
    except Exception as e:
        raise LatexConversionError(f"Unexpected error during LaTeX conversion: {str(e)}", latex_string, None, e)

def parse_parameters(parameter_str: str) -> Dict[str, sp.Symbol]:
    """Parse parameter string to create symbol dictionary"""
    if not parameter_str or parameter_str.strip() == "":
        return {}
    
    # Clean and split parameter string
    parameter_list = parameter_str.replace("$", "").replace(" ", "").replace("\\", "").split(",")
    
    # Remove any empty parameters
    parameter_list = [p for p in parameter_list if p]
    
    # Handle subscripts
    for i in range(len(parameter_list)):
        parameter_list[i] = re.sub(r'_\{((?:[^{}]|\{(?1)\})*)\}', r'\1', parameter_list[i])
    
    # Create symbol dictionary
    parameter_dict = {param: sp.symbols(param) for param in parameter_list}
    
    # Ensure lowercase epsilon gets proper handling
    if 'epsilon' in parameter_dict:
        parameter_dict['epsilon'] = sp.symbols('epsilon')
    
    return parameter_dict

def expression_to_sympy(expr_string: str, parameter_dict: Dict[str, sp.Symbol] = None) -> sp.Expr:
    """Convert expression string to SymPy expression"""
    if not expr_string or not expr_string.strip():
        raise SymPyConversionError("Empty expression provided", expr_string, "input_validation")
    
    if parameter_dict is None:
        parameter_dict = {}
        
    try:
        # Handle equals sign
        if "=" in expr_string:
            parts = expr_string.split("=")
            if len(parts) > 2:
                raise SymPyConversionError("Multiple equals signs found", expr_string, "equals_handling")
            expr_string = parts[1].strip()
            
        # Handle comma
        if ',' in expr_string:
            parts = expr_string.split(',')
            if len(parts) > 2:
                raise SymPyConversionError("Multiple commas found", expr_string, "comma_handling")
            expr_string = parts[0].strip()
            
        if not expr_string:
            raise SymPyConversionError("Expression is empty after splitting", expr_string, "post_split")
            
        # Parse expression
        transformations = (standard_transformations + 
                         (implicit_multiplication_application,
                          convert_xor,
                          implicit_application))
        
        try:
            expr = sp.parsing.parse_expr(expr_string, local_dict=parameter_dict, transformations=transformations)
            return expr
        except Exception as e:
            raise SymPyConversionError(
                f"SymPy parsing error: {str(e)}", expr_string, "sympy_parsing", e)
            
    except SymPyConversionError:
        raise
    except Exception as e:
        raise SymPyConversionError(f"Unexpected error during conversion: {str(e)}", expr_string, "unknown", e)

def solution_to_sympy(solution_string: str, parameter_str: str = "") -> ParsingResult:
    """Process a solution string to produce SymPy expressions"""
    result = ParsingResult()
    
    try:
        # 1. Extract solution from boxed environment
        result.extracted_solutions = extract_solution(solution_string)
        
        # 2. Convert LaTeX to standard expressions
        result.intermediate_expressions = [latex_to_expression(s) for s in result.extracted_solutions]
        
        # 3. Parse parameters
        result.parameter_dict = parse_parameters(parameter_str)
        
        # 4. Convert to SymPy expressions
        result.sympy_expressions = [expression_to_sympy(s, result.parameter_dict) 
                                   for s in result.intermediate_expressions]
        
        return result
    
    except ParseError as e:
        result.error_message = str(e)
        return result
    except Exception as e:
        result.error_message = f"Unexpected error: {str(e)}"
        return result

def evaluate_expression(expr: sp.Expr, parameter_dict: Dict[sp.Symbol, Any]) -> Any:
    """Evaluate a SymPy expression with given parameters"""
    try:
        result = expr.subs(parameter_dict).evalf()
        return result
    except Exception as e:
        raise EvaluationError(f"Failed to evaluate expression: {str(e)}", expr, parameter_dict, e)
    
def evaluate_solution(solution_str: str, parameter_str: str = "") -> ParsingResult:
    """Full pipeline to evaluate a solution with parameters"""
    # Parse solution to SymPy
    result = solution_to_sympy(solution_str, parameter_str)
    if not result.success:
        return result
        
    # Set random seed for reproducible parameter values
    np.random.seed(42)
    
    try:
        # Ensure x=2 if it's present
        if result.parameter_dict and 'x' in result.parameter_dict:
            parameter_values = {symbol: np.random.uniform(1, 2) for symbol in result.parameter_dict.values()}
            parameter_values[result.parameter_dict['x']] = 2
        else:
            parameter_values = {symbol: np.random.uniform(1, 2) for symbol in result.parameter_dict.values()}
        # Reset random seed
        np.random.seed(None)
        
        # Evaluate each expression
        result.evaluation_results = []
        for expr in result.sympy_expressions:
            value = evaluate_expression(expr, parameter_values)
            try:
                result.evaluation_results.append(float(value))
            except TypeError:
                result.evaluation_results.append(complex(value))
        return result
        
    except ParseError as e:
        result.error_message = str(e)
        return result
    except Exception as e:
        result.error_message = f"Unexpected error during evaluation: {str(e)}"
        return result

# ===== Main Entry Point =====
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Parse and evaluate LaTeX expressions')
    parser.add_argument('expression', type=str, help='LaTeX expression to evaluate')
    parser.add_argument('--parameters', type=str, default="x", 
                       help='Comma-separated parameters (default: "x")')
    
    args = parser.parse_args()
    
    # Run the full pipeline
    result = evaluate_solution(args.expression, args.parameters)
    
    if result.success:
        print(f"Extracted solutions: {result.extracted_solutions}")
        print(f"Intermediate expressions: {result.intermediate_expressions}")
        print(f"SymPy expressions: {result.sympy_expressions}")
        print(f"Evaluation results: {result.evaluation_results}")
    else:
        print(f"Error: {result.error_message}")
        exit(1)