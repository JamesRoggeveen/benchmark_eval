import regex as re
# Replace unicode characters with LaTeX commands (common in LLM responses, sourced from matharena)
unicode_replacement_rules = {
    r"\u23a7": r"\\boxed{",
    r"\u23ab": r"}",
    r"\n\u2502": r"\\boxed{",
    r"\u2502": r"}",
    r"\n\u2503": r"\\boxed{",
    r"\u2503": r"}",
    r"\n\uf8f0": r"\\boxed{",
    r"\uf8fb": r"}",
    r"\u221a": r"\\sqrt",
    r"\u00d7": r"\\cdot",
    r"\u202f": r" "
}

# Delete extraneous LaTeX formatting
deletion_rules = [
    r"\\left",
    r"\\right",
    r"\\Bigl",
    r"\\Bigr",
    r"\\bigl",
    r"\\bigr",
    r"\\Biggl",
    r"\\Biggr",
    r"\\hline",
    r"\\vline",
    r"$",
    r"\\hline",
    r"\\vline",
    r"\\pm",
    r"\\langle",
    r"\\rangle"
]

# Replace LaTeX formatting with expression formatting
replacement_rules = {
    r'\\approx': r'=',
    r'\\sim': r'=',
    r'\\{': r'(',
    r'\\}': r')',
    r'\[': r'(',
    r'\]': r')'
}

# Rewrite LaTeX syntax to Sympy syntax for functions
function_rules ={
    r'exp' : r'E^',
    r'\\cdot' : r'*',
    r'\\times' : r'*',
    r'\\pi':r'pi',
    r'\\i':r'I',
    r'\\(sin|cos|tan|csc|sec|cot|sinh|cosh|tanh|coth|sech|csch)\^\{-1\}': r'arc\1',
    r'arc(sin|cos|tan|csc|sec|cot|sinh|cosh|tanh|coth|sech|csch)': r'a\1',
    r'(?:\\)?(sin|cos|tan|csc|sec|cot|sinh|cosh|tanh|coth|sech|csch)\^(?:\{)?2(?:\})?': r'sq\1'
}

# Format nested LaTeX expressions by repeatedly evaluating rules, stopping when no changes are made
nested_rules = {
    r'\\frac\{([^{}]*)\}\{([^{}]*)\}' : r'(\1)/(\2)',
    r'\\sqrt\[(.*?)\]\{([^{}]*)\}' : r'(\2)**(1/(\1))',
    r'\\sqrt\{([^{}]*)\}' : r'(\1)**(1/2)',
    r'\^\{([^{}]*)\}' : r'^(\1)',
    r'\\mathrm\{([^{}]*)\}' : r'\1',
    r'\\text\{([^{}]*)\}' : r'\1'
}

# Rules to apply once nested LaTeX expressions are fully converted
final_rules = {
    r'\\Gamma\((.*?)\)': r'gamma(\1)',
    r'(?<![a-zA-Z])e(?![a-zA-Z])': r'E',
    r'([a-zA-Z])e\^': r'\1*E^',  # Handle cases like Be^{4} -> B*E^{4}
    r'\{': r'(',
    r'\}': r')',
    r'\[': r'(',
    r'\]': r')'
}

intermediate_functions = {
    'sqsin':'sin', 'sqcos':'cos', 'sqtan':'tan', 'sqcsc':'csc', 'sqsec':'sec', 'sqcot':'cot',
    'sqsinh':'sinh', 'sqcosh':'cosh', 'sqtanh':'tanh', 'sqcoth':'coth', 'sqsech':'sech', 'sqcsch':'csch'
}

# List of known functions to be handled by Sympy
sympy_functions = [
    'sin', 'cos', 'tan', 'csc', 'sec', 'cot',
    'sinh', 'cosh', 'tanh', 'coth', 'sech', 'csch',
    'asin', 'acos', 'atan', 'acsc', 'asec', 'acot',
    'asinh', 'acosh', 'atanh', 'acoth', 'asech', 'acsch',
    'log', 'ln', 'exp', 'sqrt', 'gamma'
]

known_functions = sympy_functions + list(intermediate_functions.keys())

SUPERSCRIPTS = ['dagger', 'prime']

mod_pattern = (
    r"_\{[^}]+\}"                                   # subscript {...}
    r"|_[\\][A-Za-z]+"                              # subscript command (\uparrow)
    r"|_[^\^_\{\}\s]"                               # single-char subscript
    r"|\^\{\\(?:" + "|".join(SUPERSCRIPTS) + r")\}" # allowed superscript {...}
    r"|\^\\(?:"   + "|".join(SUPERSCRIPTS) + r")"   # allowed superscript single
    r"|'+"
    r"|\^\{[^}]+\}"                                 # any other superscript {...}
    r"|\^[^\^_\{\}\s]"                              # any other superscript single
)
subsup_rewrite_pattern = re.compile(rf"(?P<base>\\?[A-Za-z]+)(?P<mods>(?:{mod_pattern})+)")

subsup_pattern = re.compile(
    r"('+)"                                          # g1: apostrophes
    r"|_\{([^}]+)\}"                                 # g2: subscript {...}
    r"|_\\([A-Za-z]+)"                               # g3: subscript command
    r"|_([^\^_\{\}\s])"                              # g4: simple subscript
    r"|\^\{\\(" + "|".join(SUPERSCRIPTS) + r")\}"    # g5: allowed sup {...}
    r"|\^\\("    + "|".join(SUPERSCRIPTS) + r")"     # g6: allowed sup simple
    r"|\^\{([^}]+)\}"                                # g7: generic sup {...}
    r"|\^([^\^_\{\}\s])"                            # g8: generic sup char
)