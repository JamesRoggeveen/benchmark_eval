import os
import sympy
from sympy.parsing.latex.lark import LarkLaTeXParser, TransformToSymPyExpr
import re
from sympy.physics.quantum.dagger import Dagger
from sympy.external import import_module
_lark = import_module("lark")

##### Parsing latex #####
# Extension to the sympy built-in lark parser:
# 1. Noncommutative symbols, specified by "parameter"
# 2. Summation over subscripts

def generate_parameter_exclusion(symbols):
    """
    Given a list of single-letter symbols to treat as variables (not functions),
    returns the %declare/%override block for the Lark grammar.
    """
    exclude_class = f"[{''.join(symbols)}]" if len(symbols) > 1 else symbols[0]
    # Negative lookahead regex: /(?![xy])[A-Za-z]/
    regex = f"/(?!{exclude_class})[A-Za-z]/"
    # Construct the modification string
    modification = (
        "%declare FUNCTION_NAME\n"
        f"%override FUNCTION_NAME: {regex}\n"
        "%override function_applied: (FUNCTION_NAME | multi_letter_symbol) \"(\" list_of_expressions \")\""
    )
    return modification

class CMT_LarkLaTeXParser(LarkLaTeXParser):
    """ Extend the built-in `LarkLaTeXParser` in `sympy` to expose `grammar_dir_path` as a parameter to allow customized grammar files."""
    def __init__(self, print_debug_output=False, transform=True, grammar_file=None, transformer=None,grammar_dir_path=None):
        """ Extend the built-in LarkLaTeXParser to expose `grammar_dir_path` as a parameter to allow customized grammar files.
        """
        if grammar_dir_path is None:
            grammar_dir_path = os.path.join(os.path.dirname(__file__), "grammar/")

        if grammar_file is None:
            with open(os.path.join(grammar_dir_path, "latex.lark"), encoding="utf-8") as f:
                latex_grammar = f.read()
        else:
            with open(grammar_file, encoding="utf-8") as f:
                latex_grammar = f.read()
        
        self.parser = _lark.Lark(
            latex_grammar,
            import_paths=[grammar_dir_path],
            parser="earley",
            start="latex_string",
            lexer="auto",
            ambiguity="resolve",
            propagate_positions=False,
            maybe_placeholders=False,
            keep_all_tokens=True)

        self.print_debug_output = print_debug_output
        self.transform_expr = transform

        if transformer is None:
            self.transformer = TransformToSymPyExpr()
        else:
            self.transformer = transformer()


class NonCommTransformer(TransformToSymPyExpr):
    def __init__(self, noncomm, **kw):
        super().__init__(**kw)
        # normalize to drop leading “\” if present
        self.noncomm = {n.lstrip("\\") for n in noncomm}

    def SYMBOL(self, token):
        name = token.value
        return sympy.Symbol(name, commutative=(name not in self.noncomm))

    def GREEK_SYMBOL(self, token):
        name = token.value
        return sympy.Symbol(name, commutative=(name not in self.noncomm))
    
    def BASIC_SUBSCRIPTED_SYMBOL(self, tokens):
        base, sub = tokens.value.split("_")
        base = sympy.Symbol(base, commutative=(base not in self.noncomm))
        if sub.startswith("{"):
            sub = sub[1:-1]
        idxs = sub.split(",")
        if isinstance(base, sympy.Symbol):
            arr = sympy.IndexedBase(base.name, commutative=base.is_commutative)
        else:
            arr = base.base
        idxed = arr[tuple(idxs)]
        return idxed

    def GREEK_SUBSCRIPTED_SYMBOL(self, tokens):
        greek_letter, sub = tokens.value.split("_")
        greek_letter = re.sub("var", "", greek_letter[1:])
        base = sympy.Symbol(greek_letter, commutative=(greek_letter not in self.noncomm))
        if sub.startswith("{"):
            sub = sub[1:-1]
        idxs = sub.split(",")
        if isinstance(base, sympy.Symbol):
                arr = sympy.IndexedBase(base.name, commutative=base.is_commutative)
        else:
            arr = base.base
        idxed = arr[tuple(idxs)]
        return idxed
        

    def superscript(self, tokens):
        if hasattr(tokens[-1], 'type') and tokens[-1].type == 'DAGGER' or hasattr(tokens[-2], 'type') and tokens[-2].type == 'DAGGER':
            return Dagger(tokens[0])
        else:
            return super().superscript(tokens)


def parse_latex_lark(s, noncomm_vars = [], debug=False):
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    # Get the directory containing the current script file
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = CMT_LarkLaTeXParser(grammar_dir_path = current_script_dir, transformer=lambda: NonCommTransformer(noncomm_vars), print_debug_output=debug)
    try:
        return parser.doparse(s)
    except Exception as e:
        raise ValueError(f"Failed to parse LaTeX string: {s}") from e
    
def parse_noncomm_str(noncomm_str):
    """
    Expect a string of the form `$x,y,z$`
    """
    if len(noncomm_str) == 0:
        return []
    if noncomm_str.startswith("$") and noncomm_str.endswith("$"):
        noncomm_str = noncomm_str[1:-1]
        return noncomm_str.split(",")
    else:
        raise ValueError("Noncommutative variables must be enclosed in $ symbols")

##### Handle Noncommutative algebra #####

def extract_noncommutative_operators(expr):
    """Extract all non-commutative operators from an expression"""
    nc_operators = []
    
    def visit_node(node):
        # Check for non-commutative Symbol
        if isinstance(node, sympy.Symbol) and not node.is_commutative:
            if node not in nc_operators:
                nc_operators.append(node)
        
        # Check for Indexed with non-commutative base
        elif isinstance(node, sympy.Indexed):
            base = node.base
            # IndexedBase always has the symbol as its first argument
            if base.args:
                base_symbol = base.args[0]
                if not base_symbol.is_commutative:
                    if node not in nc_operators:
                        nc_operators.append(node)
        
        # Recursively visit children, but skip Dagger
        if not isinstance(node, Dagger):
            if hasattr(node, 'args'):
                for arg in node.args:
                    visit_node(arg)
    
    visit_node(expr)
    return nc_operators

# For now, only fermionic (anticommutative) operators are supported {c_i,c_j^\dagger}=\delta_{ij}
# Bosonic operators are similar logic and will be implemented when we see a question requiring it
def create_fermionic_rules(operators):
    # Use `operators` the list of noncommutative operators, as the natural order
    normalorder = operators
    # Consider the normal ordering including Dagger
    normalorder_dag = [Dagger(op) for op in normalorder]

    # Reverse the order of the operators
    normalorder_rule = [(normalorder_dag[i]*normalorder_dag[j],-normalorder_dag[j]*normalorder_dag[i],) for i in range(len(normalorder_dag)) for j in range(i,len(normalorder_dag)) if j>i ] + [(normalorder[i]*normalorder[j],-normalorder[j]*normalorder[i])  for i in range(len(normalorder)) for j in range(i,len(normalorder)) if j>i] + [(normalorder[i]*normalorder_dag[j],-normalorder_dag[j]*normalorder[i]) if j!=i else (normalorder[i]*normalorder_dag[j],1-normalorder_dag[j]*normalorder[i]) for i in range(len(normalorder)) for j in range(len(normalorder))]

    return normalorder_rule

def recursiveapply(expr,subs):
    expr1=expr.subs(subs)
    counter=0
    while not expr1== expr:
        expr=expr1
        expr1=expr.subs(subs).expand()
        counter+=1
        if counter>100:
            raise ValueError("Infinite loop in recursiveapply")
    return expr1

def simplify_fermion(expr):
    ops = extract_noncommutative_operators(expr)
    if len(ops) == 0:
        return expr
    else:
        rules = create_fermionic_rules(ops)
        expr = recursiveapply(expr,rules)
        return expr

### Comparison functions ###
def parse_latex_dollar(expr, source=""):
    """
    Parse a latex expression in the form of $...$.
    """
    if expr.startswith("$") and expr.endswith("$"):
        return expr[1:-1]
    else:
        return expr

def isequal_symbolics(latex_expr_1:str, solution_string:str, noncomm_str:str=""):
    """
    Compare the LLM output with the ground truth for symbolic expressions, provided in latex format. The noncomm_str is a string of the form $x,y,z$.
    """ 
    latex_expr_1 = parse_latex_dollar(latex_expr_1,source="LLM output")
    solution_string = parse_latex_dollar(solution_string,source="provided solution")
    noncomm_vars=parse_noncomm_str(noncomm_str)
    try:
        parsed_expression_1 = parse_latex_lark(latex_expr_1, noncomm_vars = noncomm_vars)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM output: {latex_expr_1}") from e
        return False
        
    try:
        parsed_solution = parse_latex_lark(solution_string, noncomm_vars = noncomm_vars)
    except Exception as e:
        raise ValueError(f"Failed to parse provided solution: {solution_string}") from e

    try:
        diff=(parsed_expression_1 - parsed_solution).doit()
    except Exception as e:
        raise ValueError(f"Failed to compute difference between LLM output and provided solution: {str(e)}") from e

    try:
        diff = simplify_fermion(diff).simplify()
        return diff == 0
    except Exception as e:
        raise ValueError(f"Failed to simplify difference between LLM output and provided solution: {str(e)}") from e
        return False

# TODO: Actually I realized the previous numerics can also be embeeded in this framework, because "non-commutative" is a super-set of "commutative" algebra


def parse_set_list(string:str):
    if string.startswith(r"{") and string.endswith(r"}") or string.startswith(r"[") and string.endswith(r"]"):
        strings = string[1:-1].split(';')
        if string.startswith(r"{"):
            strings = {s.strip() for s in strings}
        else:
            strings = [s.strip() for s in strings]
    else:
        strings = {string}
    return strings

def isequal_symbolics_set(latex_exprs:str, solution_strings:str, noncomm_str:str=""):
    """
    Directly compare the LLM output with the ground truth for symbolic expressions, provided in latex format (with $). The noncomm_str is a string of the form $x,y,z$.
    """
    from src.parser_cmt import extract_boxed_equations
    from functools import partial

    try:
        LLM_output = extract_boxed_equations(latex_exprs)
    except ValueError as e:
        raise ValueError(f"Error in extracting boxed equations: {e}")
        return False

    
    
    LLM_outputs = parse_set_list(LLM_output)
    solutions = parse_set_list(solution_strings)
    # return solutions, LLM_outputs
    if len(LLM_outputs) != len(solutions):
        return False
    if type(LLM_outputs) != type(solutions):
        return False
    if  isinstance(LLM_outputs, list):
        for LLM_output, solution in zip(LLM_outputs, solutions):
            if not isequal_symbolics(LLM_output, solution, noncomm_str=noncomm_str):
                return False
        return True
    
    # Set is a bit tricky, because if we can reduce both expressions to a "canonical form", we can directly hash and compare them, using `Counter`. However, I don't know what can be used as a general canonical form here. Plus, is this mathematically true that `canonical(a-b)==0` <-> `canonical(a)==canonical(b)`? 
    # So I am trying a greedy approach of O(n^2) in the worst scenario.
    if isinstance(LLM_outputs, set):
        isequal_partial = partial(isequal_symbolics, noncomm_str=noncomm_str)
        return are_sets_equal_greedy(LLM_outputs, solutions, isequal_partial)


def are_sets_equal_greedy(set1, set2, isequal):
    """Greedy approach to test equality of two sets with transitivity in `isequal`"""
    if len(set1) != len(set2):
        return False
    
    list1 = list(set1)
    list2 = list(set2)
    
    for item1 in list1:
        found = False
        for i, item2 in enumerate(list2):
            if isequal(item1, item2):
                list2.pop(i)
                found = True
                break
        if not found:
            return False
    
    return True
        
        

    
    






