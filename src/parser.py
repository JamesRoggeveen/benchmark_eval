import sympy as sp
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application, convert_xor, split_symbols_custom, _token_splittable
import regex as re
import itertools
import numpy as np
import argparse
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from src.parser_rules import deletion_rules, replacement_rules, function_rules, nested_rules, final_rules, known_functions, intermediate_functions, subsup_rewrite_pattern, subsup_pattern

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
    parameter_values: Optional[Dict[sp.Symbol, Any]] = None
    evaluation_results: Optional[List[Any]] = None
    function_dict: Optional[Dict[str, sp.Function]] = None

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
            
        # Handle sympy symbols in parameter_values
        if result_dict['parameter_values']:
            param_values = {}
            for key, value in result_dict['parameter_values'].items():
                # Convert sympy symbols to strings
                if isinstance(key, sp.Symbol):
                    key = str(key)
                param_values[key] = value
            result_dict['parameter_values'] = param_values

        if result_dict['function_dict']:
            param_dict = {}
            for key, value in result_dict['function_dict'].items():
                # Convert sympy symbols to strings
                if isinstance(key, sp.Function):
                    key = str(key)
                param_dict[key] = str(value)
            result_dict['function_dict'] = param_dict
        
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
        current_string = preprocess_super_and_sub(latex_string)

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
        function_pattern = fr'(?:\\)?({"|".join(known_functions)})(?![a-zA-Z])\s*([^{{}}\s()+\-*\/^]+)'
        current_string = re.sub(function_pattern, r' \1(\2)', current_string)

        # Replace intermediate functions with the square of the argument of the function to solve issues like cos^2 x not parsing. This needs to be done after the implicit application is resolved. Thus, we use intermediate functions to earlier replace all instances of squared trig functions with another name.
        for function, replacement in intermediate_functions.items():
            pattern = re.compile(
                fr'{function}(?P<content>(?P<paren>\((?:[^()]+|(?&paren))*\)))'
            )
            current_string = pattern.sub(fr'{replacement}\g<content>^2', current_string)

        # Apply replacement rules
        for pattern, replacement in replacement_rules.items():
            current_string = re.sub(pattern, replacement, current_string)
        
        # Remove remaining backslashes
        current_string = re.sub(r'\\', ' ', current_string)
        
        # Final validation
        if not current_string.strip():
            raise LatexConversionError("Conversion resulted in empty string", latex_string)
            
        return current_string
        
    except LatexConversionError:
        raise
    except Exception as e:
        raise LatexConversionError(f"Unexpected error during LaTeX conversion: {str(e)}", latex_string, None, e)

def rewrite_super_and_sub(m):
    base = m.group('base')
    mods = m.group('mods')

    raw_subs = []
    raw_sups = []
    raw_exps = []

    for gm in subsup_pattern.finditer(mods):
        if gm.group(1):  # apostrophes
            raw_sups.extend(['prime'] * len(gm.group(1)))
        elif gm.group(2):  # braced subscript {…}
            # split on commas and strip any backslash
            for part in re.split(r'\s*,\s*', gm.group(2)):
                raw_subs.append(part.lstrip('\\'))
        elif gm.group(3) or gm.group(4):  # single‐token subscript
            tok = (gm.group(3) or gm.group(4)).lstrip('\\')
            raw_subs.append(tok)
        elif gm.group(5) or gm.group(6):  # allowed superscripts
            tok = (gm.group(5) or gm.group(6)).lstrip('\\')
            raw_sups.append(tok)
        else:  # generic exponent
            tok = (gm.group(7) or gm.group(8))
            raw_exps.append(tok)

    # 4. Deduplicate subscripts (keep first seen)
    subs_unique = []
    for tok in raw_subs:
        if tok not in subs_unique:
            subs_unique.append(tok)

    # 5. Deduplicate superscripts except allow repeated ‘prime’
    sups_unique = []
    for tok in raw_sups:
        if tok == 'prime' or tok not in sups_unique:
            sups_unique.append(tok)

    # 6. Reassemble: subscripts, allowed sups, then exponents
    name = base
    for tok in subs_unique:
        name += f"_{tok}"
    for tok in sups_unique:
        name += f"_{tok}"
    for tok in raw_exps:
        name += f"^{{{tok}}}"

    return name

def preprocess_super_and_sub(s: str) -> str:
    new_string = subsup_rewrite_pattern.sub(rewrite_super_and_sub, s)
    return normalize_backslashes(new_string).strip()

def string_permutations(templates: List[str],
                        index_rules: Dict[str, List[str]]
                       ) -> List[str]:
    """
    Given templates like ['a_i_j','U'] and 
    index_rules={'i':['1','2'], 'j':['1','2','3']},
    returns ['a_1_1','a_1_2',…,'a_2_3','U'] (U is untouched).
    """
    # 1) One regex per index to match "_i" only when followed by "_", "(" or end
    idx_patterns = {
        idx: re.compile(rf'_{re.escape(idx)}(?=(?:_|$|\())')
        for idx in index_rules
    }
    keys = list(index_rules.keys())

    result = []
    for base in templates:
        # 2) figure out which indices actually appear in this template
        present = [idx for idx in keys if idx_patterns[idx].search(base)]
        if not present:
            # no indexed placeholders here → leave it alone
            result.append(base)
            continue

        # 3) build only the necessary Cartesian product
        combos = itertools.product(*(index_rules[idx] for idx in present))
        for combo in combos:
            s = base
            # 4) do each replacement via a lambda to preserve the underscore
            for idx, val in zip(present, combo):
                pat = idx_patterns[idx]
                s = pat.sub(lambda m, v=val: f'_{v}', s)
            result.append(s)

    return result

def find_index_rules(string: str):
    idx_sets = re.findall(
        r'\(\s*([A-Za-z]\w*)\s*,\s*([^)]+?)\s*\)',
        string
    )
    index_rules = {}
    for idx, values in idx_sets:
        # values is a string like r"\uparrow,\downarrow"
        index_rules[idx] = [v.lstrip('\\') for v in re.split(r'\s*,\s*', values)]

    #  Remove those index-rule substrings from the main text
    string = re.sub(
        r',?\s*\(\s*[A-Za-z]\w*\s*,\s*[^(),]+(?:\s*,\s*[^(),]+)*\s*\)',
        '',
        string
    )
    return string, index_rules

def normalize_backslashes(s: str) -> str:
    # turn '\\\\dagger' or '\\\\\\dagger' -> '\\dagger'
    return re.sub(r'\\\\+', r'\\', s)

def extract_symbol_and_nc_lists(function_str: str):
    # 1) Extract and remove NC-flags
    nc_raw = re.findall(r'\(\s*(.+?)\s*,\s*NC\s*\)', function_str)
    function_str = re.sub(r'\(\s*.+?\s*,\s*NC\s*\)', '', function_str)
    function_str, index_rules = find_index_rules(function_str)
    
    # 3) Split on commas to get just the raw function tokens
    raw_funcs = [tok.strip() for tok in function_str.replace('$','').split(';') if tok.strip()]
    nc_raw   = [tok.strip() for tok in nc_raw if tok.strip()]

    # 4) **Normalize backslashes**, then canonicalize
    normalized = [normalize_backslashes(f) for f in raw_funcs]
    can_funcs  = [preprocess_super_and_sub(f) for f in normalized]

    normalized_nc = [normalize_backslashes(f) for f in nc_raw]
    can_nc        = [preprocess_super_and_sub(f) for f in normalized_nc]
    # 5) Expand every canonical template against the index_rules
    all_funcs = string_permutations(can_funcs, index_rules)
    nc_funcs  = string_permutations(can_nc, index_rules)

    all_funcs = all_funcs + nc_funcs
    nc_funcs = set(nc_funcs)

    return all_funcs, nc_funcs

def parse_functions(function_str: str):
    all_funcs, nc_funcs = extract_symbol_and_nc_lists(function_str)
    function_dict = {}
    for name in all_funcs:
        is_nc = (name in nc_funcs)
        function_dict[name] = sp.Function(name, commutative=not is_nc)

    return function_dict

def parse_parameters(parameter_str: str):
    # parameter_str, index_rules = find_index_rules(parameter_str)
    # can_params = [preprocess_super_and_sub(tok) for tok in parameter_str.replace('$','').split(';') if tok.strip()]
    # can_params = [f.replace("\\","") for f in can_params]
    # all_params = string_permutations(can_params, index_rules)
    all_params, nc_params = extract_symbol_and_nc_lists(parameter_str)
    # for the moment remove all backslashes from parameter names
    all_params = [f.replace("\\","") for f in all_params]
    nc_params = set([f.replace("\\","") for f in nc_params])
    parameter_dict = {}
    for name in all_params:
        is_nc = (name in nc_params)
        parameter_dict[name] = sp.Symbol(name, commutative=not is_nc)
    return parameter_dict
    
def expression_to_sympy(expr_string: str, local_dict: Dict[str, sp.Symbol] = None) -> sp.Expr:
    """Convert expression string to SymPy expression"""
    if not expr_string or not expr_string.strip():
        raise SymPyConversionError("Empty expression provided", expr_string, "input_validation")
    
    if local_dict is None:
        local_dict = {}
        
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
        
        
        expr_string = re.sub(r'\s{2,}', ' ', expr_string)
        # Parse expression with enhanced transformations
        transformations = (standard_transformations + 
                         (implicit_multiplication_application,
                          convert_xor))
        try:
            expr = sp.parsing.parse_expr(expr_string, local_dict=local_dict, transformations=transformations)
            return expr
        except Exception as e:
            raise SymPyConversionError(
                f"SymPy parsing error: {str(e)}", expr_string, "sympy_parsing", e)
            
    except SymPyConversionError:
        raise
    except Exception as e:
        raise SymPyConversionError(f"Unexpected error during conversion: {str(e)}", expr_string, "unknown", e)

def solution_to_sympy(solution_string: str, parameter_str: str = "", function_str: str = "") -> ParsingResult:
    """Process a solution string to produce SymPy expressions"""
    result = ParsingResult()
    
    try:
        # 1. Extract solution from boxed environment
        result.extracted_solutions = extract_solution(solution_string)
        
        result.parameter_dict = parse_parameters(parameter_str)
        result.function_dict = parse_functions(function_str)
        local_dict = {**result.parameter_dict, **result.function_dict}
        # 2. Convert LaTeX to standard expressions
        result.intermediate_expressions = [latex_to_expression(s) for s in result.extracted_solutions]
        
        # 4. Convert to SymPy expressions
        result.sympy_expressions = [expression_to_sympy(s, local_dict) 
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
    """Full pipeline to evaluate a solution with parameters into a numeric result"""
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
        
        # Store the actual parameter values used in the evaluation
        result.parameter_values = parameter_values
        
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