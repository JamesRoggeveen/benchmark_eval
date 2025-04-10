from typing import List, Optional
from dataclasses import dataclass

@dataclass
class TestParserData:
    solution_string:str
    parameter_string:str
    expected_evaluation: List[float]
    description: Optional[str] = None

test_data = [
    TestParserData(
        solution_string="$\\boxed{1;2;3}$",
        parameter_string="",
        expected_evaluation=[1,2,3],
        description="Basic boxed solution with multiple constant values"
    ),
    TestParserData(
        solution_string="$\\boxed{x;x^2;x^3}$",
        parameter_string="x",
        expected_evaluation=[2,4,8],
        description="Polynomial expressions with variable x where x=2"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x)= \\sinh^{-1}(\\frac{x}{0.24}) * (\\frac{1}{x}) }$",
        parameter_string="x",
        expected_evaluation=[1.4085],
        description="Inverse hyperbolic sine function with fraction"
    ),
    TestParserData(
        solution_string="$\\boxed{ y(x) = e^{-1} -Ei(-1)}$",
        parameter_string="x",
        expected_evaluation=[0.587263],
        description="Expression with exponential and exponential integral"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) =(-\\tan^{-1}((-5-x) + \\pi/2)) (\\tan^{-1}(1/2 \\arctan{(-5-x)} + \\pi/4) + 5 + x); y(x)=20(-\\tan^{-1}((-5-x)+ \\pi/2))}$",
        parameter_string="x",
        expected_evaluation=[9.8189,27.773],
        description="Multiple expressions with nested inverse tangent functions"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = (2*\\sqrt{3*x} + 3*\\sqrt{x})/(2x*\\sqrt{3*x})}$",
        parameter_string="x",
        expected_evaluation=[0.933013],
        description="Rational expression with multiple square roots"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x)=1-x\\ln x}$",
        parameter_string="x",
        expected_evaluation=[-0.386294],  
        description="Expression with natural logarithm and implicit multiplication"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = \\sin^{-1}(x)/x}$",
        parameter_string="x",
        expected_evaluation=[0.785398 - 0.658479j],  
        description="Inverse sine function resulting in complex value"
    ),
    TestParserData(
        solution_string="$\\boxed{y = -\\frac{1}{x\\ln x}}$",
        parameter_string="x",
        expected_evaluation=[-0.721348], 
        description="Negative reciprocal with natural log in denominator"
    ),
    TestParserData(
        solution_string="$\\boxed{y = \\frac{24\\pi\\sqrt{2\\pi}}{36\\pi^{2}+\\pi^{4}+48}x^{-1/2}e^{x}}$",
        parameter_string="x",
        expected_evaluation=[1.97213],
        description="Complex fraction with pi, square root, and exponential terms"
    ),
    TestParserData(
        solution_string="$\\boxed{y = \\sqrt{\\frac{4\\pi}{x(5-\\sqrt{5})}} \\exp\\Biggl[-x\\Bigl(\\frac{3-\\sqrt{5}}{4}-\\ln\\Bigl(\\frac{1+\\sqrt{5}}{2}\\Bigr)\\Bigr)\\Biggr]}$",
        parameter_string="x",
        expected_evaluation=[2.69411],
        description="Nested expression with square roots, fractions, and exponential"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = 2.60204081632653\\cdot(1.51015101510151 - x)^(4/7)+0.3762550156073181}$",
        parameter_string="x",
        expected_evaluation=[-0.00884867 + 1.68725j],
        description="Decimal coefficients with rational exponent yielding complex result"
    ),
    TestParserData(
        solution_string="$\\boxed{y = (-14.88 \\cdot x)^(\\frac{1}{7}) }$",
        parameter_string="x",
        expected_evaluation=[1.46295 + 0.704518j],
        description="Negative base raised to fractional power yielding complex result"
    ),
    TestParserData(
        solution_string="$\\boxed{y= \\exp{ \\frac{x (x - 1)}{2} } \\cos( x \\arccos( \\frac{1}{\\sqrt{e}} ) ) }$",
        parameter_string="x",
        expected_evaluation=[-0.718282],
        description="Product of exponential and cosine of inverse cosine expression"
    ),
    TestParserData(
        solution_string="$\\boxed{y = \\frac{\\exp{(x (2^{2/3} - 1))-1}}{x^{1.5}}}$",
        parameter_string="x",
        expected_evaluation=[0.421086],
        description="Exponential with cube root of 2 divided by x to power 1.5"
    ),
    TestParserData(
        solution_string="$\\boxed{y = \\exp(-\\frac{1}{\\sqrt{x + 1}})(x + 1 - \\frac{x + 1}{(1 + \\sqrt{x + 1})^2})}$",
        parameter_string="x",
        expected_evaluation=[1.45852],
        description="Product of exponential and rational expression with square roots"
    ),
    TestParserData(
        solution_string="$\\boxed{y = -4\\ln(0.8055108539113272 - x) + \\ln(\\frac{24}{\\sin (0.8055108539113272)}) }$",
        parameter_string="x",
        expected_evaluation=[2.79404 - 12.5664j],
        description="Logarithmic expression with sine function yielding complex result"
    ),
    TestParserData(
        solution_string="$\\boxed{y = \\frac{1}{e^{-x}}}$",
        parameter_string="x",
        expected_evaluation=[7.38906],
        description="Reciprocal of negative exponential (equivalent to e^x)"
    ),
    TestParserData(
        solution_string="$\\boxed{y = \\sqrt[3]{\\frac{1}{e^{x}}}}$",
        parameter_string="x",
        expected_evaluation=[0.513417],
        description="Cube root of reciprocal exponential (e^(-x/3))"
    ),
    TestParserData(
        solution_string="$\\boxed{u = m\\left(\\frac{2}{r^3} - \\frac{5}{a^3} + \\frac{3r^2}{a^5}\\right)\\cos \\theta; v = m\\left(\\frac{1}{r^3}+\\frac{5}{a^3}-\\frac{6r^2}{a^5}\\right)\\sin \\theta}$",
        parameter_string="$m, r, \\theta, a, \\psi$",
        expected_evaluation=[-0.0306499,-1.12344],
        description="Physics-related expressions with multiple variables and trigonometric functions"
    ),
    TestParserData(
        solution_string="$\\boxed{u = m \\cos \\theta \\left(\\frac{2}{r^3} - \\frac{5}{a^3} + \\frac{3r^2}{a^5}\\right); v = m\\sin \\theta\\left(\\frac{1}{r^3}+\\frac{5}{a^3}-\\frac{6r^2}{a^5}\\right)}$",
        parameter_string="$m, r, \\theta, a, \\psi$",
        expected_evaluation=[-0.0306499,-1.12344],
        description="Alternative formulation of physics expressions with different order of terms"
    ),
    TestParserData(
        solution_string="$\\boxed{y = e^{\\frac{x^3}{3}} + (2-e^{1/3})e^{-(1-x)/\\epsilon}}$",
        parameter_string="$x, \\epsilon$",
        expected_evaluation=[15.4011],
        description="Sum of exponential expressions with epsilon parameter"
    ),
    TestParserData(
        solution_string="$\\boxed{y \\approx \\sqrt[3]{3} x (\\log x)^{1/3}; y \\approx -\\sqrt[3]{3} x (\\log x)^{1/3}}$",
        parameter_string="$x$",
        expected_evaluation=[2.55277, -2.55277],
        description="Gemini 2.0 Flash Thinking output on test_eval.json"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = 5\\cosh x + 5\\cos x}$",
        parameter_string="$x$",
        expected_evaluation=[16.7302],
        description="Hyperbolic cosine and cosine function"
    ),
    TestParserData(
        solution_string="$\\boxed{A e^{(x^3)/3} + (B-Ae^{-1/3})e^{-x/\\sqrt{\\epsilon}}}$",
        parameter_string="$x,\\epsilon,A,B$",
        expected_evaluation=[25.0121],
        description="Uniform boundary with bad implicit multiplication of E"
    ),
]