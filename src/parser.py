import sympy as sp
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application, convert_xor, split_symbols_custom, _token_splittable
from sympy.physics.quantum.dagger import Dagger
import regex as re
import ast
import itertools
import numpy as np
import argparse
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from src.parser_rules import deletion_rules, replacement_rules, function_rules, nested_rules, final_rules, known_functions, intermediate_functions, subsup_rewrite_pattern, subsup_pattern, sympy_symbols, beta_function_pattern, unicode_replacement_rules

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
        # boxes = re.findall(r"(boxed|fbox)\{((?:[^\{}\}]|\{(?2)\})*)\}", solution_string)
        pattern = r"(boxed|fbox)\{((?:[^\{}\}]|\{(?2)\})*)\}"
    
        # findall returns all the capture-group contents
        all_contents = re.findall(pattern, solution_string)
        # This is a little hacky
        solution_group = all_contents[-1][1] if all_contents else None
        if not solution_group:
            raise SolutionExtractionError("No boxed solution found in response")
        
        if not solution_group.strip():
            raise SolutionExtractionError("Empty solution found in boxed environment")
        
        text_wrapper = re.match(r'^\s*\\text\{(.+)\}\s*$', solution_group, re.DOTALL)
        if text_wrapper:
            solution_group = text_wrapper.group(1).strip()
            
        solution_list = solution_group.split(';')
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

def latex_to_expression(latex_string: str, local_dict: Dict[str, Union[sp.Symbol, sp.Function]] = {}) -> str:
    """Convert LaTeX string to an expression suitable for SymPy parsing"""
    if not latex_string or not latex_string.strip():
        raise LatexConversionError("Empty LaTeX string provided", latex_string)
        
    try:
        current_string = latex_string
        for pattern, replacement in unicode_replacement_rules.items():
            latex_string = re.sub(pattern, replacement, latex_string)
        current_known_functions = known_functions.copy()
        current_known_functions = sorted(current_known_functions, key=len, reverse=True)
        for pattern in deletion_rules:
            current_string = re.sub(pattern, "", current_string)

        formatting_strings = ["text","mathrm","operatorname"]
        for formatting_string in formatting_strings:
            pattern = re.compile(r'\\' + formatting_string + r'\{(' + '|'.join(map(re.escape, current_known_functions)) + r')\}')
            current_string = pattern.sub(r'\1', current_string)

        beta_formatted_string = rewrite_beta_function(current_string)
        if beta_formatted_string != current_string:
            current_string = beta_formatted_string
            current_known_functions.append("betainc")
            current_known_functions.append("beta")
        
        current_string, _integrals = shield_integrals(current_string,local_dict)
        if _integrals != {}:
            current_known_functions.append("integrate")
            current_known_functions.append("Integral")

        current_string = preprocess_super_and_sub(current_string)

        # If J is a parameter, we need to surround it with spaces to prevent it from being parsed as an imaginary number.
        if "J" in local_dict.keys():
            pattern = r'(?<![A-Za-z_])J(?![A-Za-z0-9_])'
            current_string = re.sub(pattern, r' J ', current_string)
            current_string = re.sub(r'\s+', ' ', current_string).strip()
        
        # Apply function rules
        for pattern, replacement in function_rules.items():
            current_string = re.sub(pattern, replacement, current_string)

        current_string, intermediat_funcs_list = encode_frac_powers(current_string)
        current_known_functions.extend(intermediat_funcs_list)
        # Apply nested rules iteratively until no more changes
        for _ in range(5):  # Limit iterations to prevent infinite loops
            init_string = current_string
            for pattern, replacement in nested_rules.items():
                current_string = re.sub(pattern, replacement, current_string)
            if current_string == init_string:
                break
        
        # Add additional space before known functions to prevent them from being parsed as variables (i.e. x\ln(x) -> x \ln(x))    
        pattern = re.compile(
            r'(?<![A-Za-z])\\?('
            + '|'.join(map(re.escape, current_known_functions))
            + r')(?![A-Za-z])'
        )

        # 3. Replace with " space + the bare function name "
        current_string = pattern.sub(r' \1', current_string)

        # 3) Replace with “ space + the bare function name ”
        current_string = pattern.sub(r' \1', current_string)
        # Find known functions that are using implicit application to add parentheses, i.e \sin \theta -> \sin(\theta)
        # function_pattern = fr'(?:\\)?({"|".join(current_known_functions)})(?![a-zA-Z])\s*([^{{}}\s()+\-*\/^]+)'
        # current_string = re.sub(function_pattern, r' \1(\2)', current_string)
        pattern = re.compile(
            r'(?:\\)?'                                 # optional backslash
            r'(' + '|'.join(map(re.escape, current_known_functions)) + r')'# the function (or placeholder)
            r'(?!\w)'                                  # not followed by letter/digit/_
            r'\s+'                                     # **ONE OR MORE** spaces
            r'([^{}\s()+\-*/^]+)'                      # the bare argument
        )

        # 3) replace
        current_string = pattern.sub(r'\1(\2)', current_string)
        # Replace intermediate functions with the square of the argument of the function to solve issues like cos^2 x not parsing. This needs to be done after the implicit application is resolved. Thus, we use intermediate functions to earlier replace all instances of squared trig functions with another name.
        # for function, replacement in intermediate_functions.items():
        #     pattern = re.compile(
        #         fr'{function}(?P<content>(?P<paren>\((?:[^()]+|(?&paren))*\)))'
        #     )
        #     current_string = pattern.sub(fr'{replacement}\g<content>^2', current_string)

        current_string = decode_frac_powers(current_string)
        for pattern, replacement in replacement_rules.items():
            current_string = re.sub(pattern, replacement, current_string)
        KNOW_USER_DEFINED_PARAMETERS = set(local_dict.keys())
        KNOWN_NAMES = sorted(
            set(current_known_functions) | set(KNOW_USER_DEFINED_PARAMETERS) | set(sympy_symbols) | set(_integrals.keys()),
            key=len, reverse=True
        )

        TOKEN_RE = re.compile(
            r'('
            + r'|'.join(map(re.escape, KNOWN_NAMES))  # group of known names
            + r'|[A-Za-z]'                            # or one single letter
            + r')'
        )
        current_string = lex_identifiers(current_string, TOKEN_RE)

        for pattern, replacement in final_rules.items():
            current_string = re.sub(pattern, replacement, current_string)

        current_string = re.sub(r'\\', ' ', current_string)
        current_string = re.sub(r'\s+', ' ', current_string)
        if _integrals != {}:
            current_string = unshield_integrals(current_string, _integrals)

        # Final validation
        if not current_string.strip():
            raise LatexConversionError("Conversion resulted in empty string", latex_string)
        return current_string
        
    except LatexConversionError:
        raise
    except Exception as e:
        raise LatexConversionError(f"Unexpected error during LaTeX conversion: {str(e)}", latex_string, None, e)

def encode_frac_powers(s: str):
    """
    Rewrite \func^N or \func^{\frac{M}{N}} → func_N or func_M_N,
    dropping any leading backslash.  Return (new_string, placeholders_list).
    """
    funcs_group = "|".join(intermediate_functions)
    pattern = re.compile(
        r'\\?'                          # optional leading backslash
        rf'(?:{funcs_group})'           # one of your functions
        r'\^(?:\{)?'                    # ^ or ^{
        r'(?P<pow>'                     
            r'\d+/\d+'                  #   1/2
          r'|\d+'                      #   2
          r'|\\frac\{\d+\}\{\d+\}'     #   \frac{1}{2}
        r')'
        r'(?:\})?'                      # optional closing brace
    )

    placeholders: List[str] = []
    def repl(m):
        full = m.group(0)
        # strip leading backslash and the "^..." part to find func
        func = re.match(r'\\?([a-z]+)', full).group(1)
        raw  = m.group('pow')           # e.g. "2", "1/2" or "\frac{1}{2}"
        frac = re.match(r'\\frac\{(\d+)\}\{(\d+)\}', raw)
        if frac:
            num, den = frac.groups()
        elif '/' in raw:
            num, den = raw.split('/',1)
        else:
            num, den = raw, None

        norm = f"{num}_{den}" if den else num
        ph   = f"{func}_{norm}"
        if ph not in placeholders:
            placeholders.append(ph)
        return ph

    return pattern.sub(repl, s), placeholders

def decode_frac_powers(s: str) -> str:
    """
    Replace func_N(...) or func_M_N(...) with func(...)^N or func(...)^(M/N).
    """
    paren_re  = r'(?P<content>\((?:[^()]+|(?&content))*\))'
    funcs_group = "|".join(intermediate_functions)
    decode_pat = re.compile(
        r'\b(' + funcs_group + r')_'  # func_
        r'(\d+(?:_\d+)*)'              # norm (digits or digits_digits)
        + paren_re
    )
    def _repl(m):
        func, norm, content = m.group(1), m.group(2), m.group('content')
        if '_' in norm:
            M, N = norm.split('_', 1)
            exp = f"({M}/{N})"
        else:
            exp = norm
        return f"{func}{content}^{exp}"
    return decode_pat.sub(_repl, s)
    

def rewrite_beta_function(string: str):
    def repl(m):
        a = m.group('a').strip()
        b = m.group('b').strip()
        z = m.group('z')
        if z is not None:
            # subscripted: B_{z}(a,b) → betainc(a,b,0,z)
            return f"betainc({a},{b},0,{z.strip()})"
        else:
            # plain:       B(a,b)    → beta(a,b)
            return f"beta({a},{b})"
    return beta_function_pattern.sub(repl, string)


def _parse_braces(s: str, j: int) -> Tuple[str,int]:
    """Given s[j]=='{', return ('{...}', index_after_closing_brace)."""
    assert s[j] == '{'
    depth = 0
    start = j
    L = len(s)
    while j < L:
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return s[start:j+1], j+1
        j += 1
    raise ValueError("Unbalanced braces")

def normalize_limit(lim: str) -> str:
    """Turn LaTeX infinities into Sympy oo notation."""
    t = lim.strip()
    if t in (r'\infty', 'infty'):
        return 'oo'
    if t in (r'-\infty', '-infty'):
        return '-oo'
    return t

def shield_integrals(s: str, local_dict: Dict[str, sp.Symbol]={}) -> Tuple[str, Dict[str,str]]:
    out: list[str] = []
    integrals: Dict[str,str] = {}
    counter = 0
    i, L = 0, len(s)

    while True:
        idx = s.find(r'\int_', i)
        if idx < 0:
            out.append(s[i:])
            break

        out.append(s[i:idx])
        j = idx + len(r'\int_')

        # --- parse lower limit: braces, backslash-command, or single char ---
        if j < L and s[j] == '{':
            raw_lo, j = _parse_braces(s, j)
        elif j < L and s[j] == '\\':
            m = re.match(r'\\[A-Za-z]+', s[j:])
            raw_lo = m.group(0)
            j += len(raw_lo)
        else:
            raw_lo, j = s[j], j+1

        # --- expect '^' ---
        if j < L and s[j] == '^':
            j += 1
        else:
            raise ValueError("Missing '^' after lower limit")

        # --- parse upper limit: same logic ---
        if j < L and s[j] == '{':
            raw_hi, j = _parse_braces(s, j)
        elif j < L and s[j] == '\\':  # e.g. \infty or \alpha
            m = re.match(r'\\[A-Za-z]+', s[j:])
            raw_hi = m.group(0)
            j += len(raw_hi)
        else:
            raw_hi, j = s[j], j+1


        # skip whitespace
        while j < L and s[j].isspace():
            j += 1

        # --- case A: leading \frac{dvar}{den} ---
        if s.startswith(r'\frac{d', j):
            j_frac = j + len(r'\frac')
            numb, j2 = _parse_braces(s, j_frac)       # "{dvar}"
            m = re.match(r'\{d([A-Za-z]\w*)\}', numb)
            var = m.group(1) if m else 'x'
            if j2 < L and s[j2] == '{':
                denb, j3 = _parse_braces(s, j2)
                den = denb.strip('{}')
                body = f"1/({den})"
                end_diff = j3
            else:
                body, end_diff = "", j2

        else:
            # --- case B: find first 'd<var>' anywhere, strip off the 'd'... ---
            start_body = j
            brace_depth = paren_depth = 0
            var = None
            end_diff = j

            while j < L:
                c = s[j]
                if c == '{':
                    brace_depth += 1; j += 1
                elif c == '}':
                    brace_depth -= 1; j += 1
                elif c == '(':
                    paren_depth += 1; j += 1
                elif c == ')':
                    paren_depth -= 1; j += 1
                elif c == 'd':
                    m = re.match(r'd([A-Za-z]\w*)', s[j:])
                    if m:
                        var = m.group(1)
                        end_body = j         # integrand is up to here
                        end_diff = j + m.end()
                        break
                    else:
                        j += 1
                else:
                    j += 1

            if var is None:
                var = 'x'
                end_body = j
                end_diff = j

            body = s[start_body:end_body]

        # --- record template + placeholder ---
        if r'\infty' in raw_hi:
            hi = raw_hi.replace(r'\infty', 'oo')
        else:
            hi = latex_to_expression(raw_hi, local_dict)
        if r'\infty' in raw_lo:
            lo = raw_lo.replace(r'\infty', 'oo')
        else:
            lo = latex_to_expression(raw_lo, local_dict)
        template = f"Integral({{EXPR}},({var},{lo},{hi}))"
        key = f"<INT{counter}>"
        integrals[key] = template
        counter += 1

        out.append(f"{key}{body}{key}")
        i = end_diff

    return "".join(out), integrals

def unshield_integrals(s: str, integrals: Dict[str,str]) -> str:
    for key in sorted(integrals, key=len, reverse=True):
        tmpl = integrals[key]
        patt = re.compile(re.escape(key) + r'(.*?)' + re.escape(key), re.DOTALL)
        s = patt.sub(lambda m, T=tmpl: T.replace("{EXPR}", m.group(1)), s)
    return s

    for key in sorted(integrals, key=len, reverse=True):
        tmpl = integrals[key]
        patt = re.compile(
            re.escape(key) + r'(.*?)' + re.escape(key),
            re.DOTALL
        )
        s = patt.sub(lambda mo, T=tmpl: T.replace("{EXPR}", mo.group(1)), s)

    # --- 2) Numeric‐evaluate ALL definite integrals in s ---
    #    Match integrate(some_python_expr,(var,lo,hi))
    int_re = re.compile(
        r'integrate\('
          r'(?P<expr>.+?)'              # non‐greedy up to the next comma
        r',\('
          r'(?P<var>\w+),'              # the variable
          r'(?P<lo>[^,]+),'             # lower limit
          r'(?P<hi>[^)]+)'              # upper limit
        r'\)\)',
        re.DOTALL
    )

    def _eval(m):
        # parse out the pieces
        expr_str = m.group('expr')
        var      = sp.symbols(m.group('var'))
        lo       = sp.sympify(m.group('lo'))
        hi       = sp.sympify(m.group('hi'))
        expr     = sp.sympify(expr_str)
        # do the integral and evalf
        val = sp.integrate(expr, (var, lo, hi)).evalf(15)
        # return a plain decimal literal
        return str(float(val))

    s = int_re.sub(lambda m: _eval(m), s)
    return s

def lex_identifiers(s: str, TOKEN_RE: re.Pattern) -> str:
    tokens = []
    pos = 0
    L   = len(s)
    while pos < L:
        m = TOKEN_RE.match(s, pos)
        if m:
            tok = m.group(1)
            tokens.append(('ID', tok))
            pos = m.end()
        else:
            # copy any one non-ID character as a separate token
            tokens.append(('OP', s[pos]))
            pos += 1

    # now rebuild the string, inserting '*' between ID tokens when necessary
    out = []
    prev_id = False
    for typ, tok in tokens:
        # only real IDs (not placeholders) count
        if typ=='ID' and not tok.startswith('<INT') :
            if tok in ('e','i'):
                tok = tok.upper()
            if prev_id:
                out.append('*')
            out.append(tok)
            prev_id = True
        else:
            out.append(tok)
            prev_id = False
    return ''.join(out)

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
    # Replace lambda with lam to avoid conflicts with python reserved word using replacement_rules
    for pattern, replacement in replacement_rules.items():
        function_str = re.sub(pattern, replacement, function_str)
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

def simplify_fermionic_expression(expr: sp.Expr,
    operator_dict: Dict[str, Union[sp.Symbol, sp.Function]]
) -> sp.Expr:
    """
    Normal-order only those a, a† pairs for which both forms exist
    in operator_dict, applying
      {a_i, a_j}   = 0,
      {a_i†, a_j†} = 0,
      {a_i, a_j†}  = δ_{ij},
    but only at the top-level of each term so we don't loop forever.
    The “natural” order of different modes is taken from base_heads.
    """

    # 1) collect your modes in the order you want
    valid      = [n for n in operator_dict
                  if not n.endswith('_dagger') and f"{n}_dagger" in operator_dict]
    base_heads = [operator_dict[n]           for n in valid]
    dag_heads  = [operator_dict[f"{n}_dagger"] for n in valid]

    # maps head → its position in base_heads
    idx_base = {h:i for i,h in enumerate(base_heads)}
    idx_dag  = {h:i for i,h in enumerate(dag_heads)}

    # 2) helper to pull off the “head” (Symbol or .func)
    def head(x):
        if x in base_heads or x in dag_heads:
            return x
        if hasattr(x, 'func'):
            return x.func
        return None

    # 3) one‐step rewrite for a single Mul
    def _rewrite_mul(mul: sp.Mul) -> sp.Expr:
        args = list(mul.args)
        for i in range(len(args)-1):
            A, B = args[i], args[i+1]
            hA, hB = head(A), head(B)

            # (i)  base–base: a_i a_j → − a_j a_i if out of order, zero if same
            if hA in base_heads and hB in base_heads:
                if idx_base[hA] == idx_base[hB]:
                    return sp.Integer(0)
                if idx_base[hA] > idx_base[hB]:
                    new = args[:i] + [B, A] + args[i+2:]
                    return -sp.Mul(*new)
                continue

            # (ii) dag–dag: a_i† a_j† → − a_j† a_i† if out of order, zero if same
            if hA in dag_heads and hB in dag_heads:
                if idx_dag[hA] == idx_dag[hB]:
                    return sp.Integer(0)
                if idx_dag[hA] > idx_dag[hB]:
                    new = args[:i] + [B, A] + args[i+2:]
                    return -sp.Mul(*new)
                continue

            # (iii) base–dag: a_i a_j† → δ_{ij} − a_j† a_i
            if hA in base_heads and hB in dag_heads:
                ib, jd = idx_base[hA], idx_dag[hB]
                term = (1 - B*A) if ib == jd else -B*A
                new = args[:i] + [term] + args[i+2:]
                return sp.Mul(*new)

        return mul

    # 4) drive each Mul to its fixed point
    def simplify_term(t: sp.Expr) -> sp.Expr:
        if not isinstance(t, sp.Mul):
            return t
        cur = t
        while True:
            nxt = _rewrite_mul(cur)
            if nxt == cur:
                return cur
            cur = nxt

    # 5) distribute over sums
    if expr.is_Add:
        return sum(simplify_term(term) for term in expr.args)
    else:
        return simplify_term(expr)

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
            
        # Handle comma (we need to come back to this)
        # if ',' in expr_string:
        #     parts = expr_string.split(',')
        #     if len(parts) > 2:
        #         raise SymPyConversionError("Multiple commas found", expr_string, "comma_handling")
        #     expr_string = parts[0].strip()
            
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
        result.intermediate_expressions = [latex_to_expression(s, local_dict=local_dict) for s in result.extracted_solutions]
        
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
    
def evaluate_solution(solution_str: str, parameter_str: str = "", *args, **kwargs) -> ParsingResult:
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

def parse_numeric_solution(s: str, *args, **kwargs) -> ParsingResult:
    """
    Takes tokens like ["(0, 4.19)", "48", …] and returns a ParsingResult
      - .extracted_solutions: the original token list
      - .evaluation_results: list of floats or tuples of floats
      - .error_message: aggregated parse errors (empty if all succeeded)
    """
    result = ParsingResult()
    try:
        tokens = extract_solution(s)
    except Exception as e:
        result.error_message = f"Unexpected error during parsing: {str(e)}"
        return result
    for i in range(len(tokens)):
        tokens[i] = tokens[i].split("=")[-1].strip()
    result.extracted_solutions = tokens

    parsed: List[Union[float, tuple]] = []
    errors: List[str] = []

    for tok in tokens:
        s = tok.strip()
        try:
            val = ast.literal_eval(s)
        except (SyntaxError, ValueError) as e:
            errors.append(f"Could not parse {tok!r}: {e}")
            continue

        # single number?
        if isinstance(val, (int, float)):
            parsed.append(float(val))

        # tuple of numbers?
        elif isinstance(val, tuple) and all(isinstance(x, (int, float)) for x in val):
            parsed.append(tuple(float(x) for x in val))

        else:
            errors.append(f"Parsed {tok!r} → {val!r}, but it's not a number or tuple of numbers")

    result.evaluation_results = parsed
    if errors:
        # join multiple errors into one message
        result.error_message = "; ".join(errors)

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