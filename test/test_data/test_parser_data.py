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
        parameter_string="$m; r; \\theta; a; \\psi$",
        expected_evaluation=[-0.0306499,-1.12344],
        description="Physics-related expressions with multiple variables and trigonometric functions"
    ),
    TestParserData(
        solution_string="$\\boxed{u = m \\cos \\theta \\left(\\frac{2}{r^3} - \\frac{5}{a^3} + \\frac{3r^2}{a^5}\\right); v = m\\sin \\theta\\left(\\frac{1}{r^3}+\\frac{5}{a^3}-\\frac{6r^2}{a^5}\\right)}$",
        parameter_string="$m; r; \\theta; a; \\psi$",
        expected_evaluation=[-0.0306499,-1.12344],
        description="Alternative formulation of physics expressions with different order of terms"
    ),
    TestParserData(
        solution_string="$\\boxed{y = e^{\\frac{x^3}{3}} + (2-e^{1/3})e^{-(1-x)/\\epsilon}}$",
        parameter_string="$x;\\epsilon$",
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
        parameter_string="$x;\\epsilon;A;B$",
        expected_evaluation=[25.0121],
        description="Uniform boundary with bad implicit multiplication of E"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = \\cos\\left(\\frac{1}{2\\epsilon} \\left( x\\sqrt{1+x^2} + \\text{arcsinh}(x) \\right)\\right)}$",
        parameter_string="$x;\\epsilon$",
        expected_evaluation=[0.0544603],
        description="Text values in the solution string"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = \\cos\\left(\\frac{1}{2\\epsilon} \\left( x\\sqrt{1+x^2} + \\mathrm{arcsinh}(x) \\right)\\right)}$",
        parameter_string="$x;\\epsilon$",
        expected_evaluation=[0.0544603],
        description="Text values in the solution string"
    ),
    TestParserData(
        solution_string="$\\boxed{y \\sim \\sqrt[3]{\\frac{81}{5}} x^{4/3}; y \\sim -\\sqrt[3]{\\frac{81}{5}} x^{4/3}}$$",
        parameter_string="$x$",
        expected_evaluation=[6.37595,-6.37595],
        description="Two solutions to ODE with sim"
    ),
    TestParserData(
        solution_string="$\\boxed{\\pi R \\delta_{ij}; 0; \\frac{\\pi R}{4} (\\delta_{ij}\\delta_{kl} + \\delta_{ik}\\delta_{jl} + \\delta_{il}\\delta_{jk})}$",
        parameter_string="$n; R; \\delta_{ij}; \\delta_{kl}; \\delta_{ik}; \\delta_{jl}; \\delta_{il}; \\delta_{jk}$",
        expected_evaluation=[10.614264613057003, 0, 9.314767438067218],
        description="Kronecker delta with multiple solutions without spaces"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = x^2 - 1 - \\sqrt{1 + (1 - x^2)^2} + 3 sech((\\frac{1 - x}{\\sqrt{2\\epsilon}} + \\tanh^{-1} \\sqrt{\\frac{2}{3}}))^2 + 3 sech((\\frac{1 + x}{\\sqrt{2\\epsilon}} + \\tanh^{-1} \\sqrt{\\frac{2}{3}}))^2 + 1}$$",
        parameter_string="$x;\\epsilon$",
        expected_evaluation=[3.51664963],
        description="Squared sech function"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = x^2 - 1 - \\sqrt{1 + (1 - x^2)^2} + 3 sech^2((\\frac{1 - x}{\\sqrt{2\\epsilon}} + \\tanh^{-1} \\sqrt{\\frac{2}{3}})) + 3 sech^2((\\frac{1 + x}{\\sqrt{2\\epsilon}} + \\tanh^{-1} \\sqrt{\\frac{2}{3}})) + 1}$$",
        parameter_string="$x;\\epsilon$",
        expected_evaluation=[3.51664963],
        description="Squared sech function with interior square"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = \\cos^2 x}$$",
        parameter_string="$x$",
        expected_evaluation=[0.173178],
        description="Squared cosine function"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = \\frac{1 + \\log(10)}{1 + \\cos(30) + \\sin(40)} \\exp(-\\lambda) \\sqrt{\\frac{2}{\\lambda}}}$",
        parameter_string="$x; \\lambda$",
        expected_evaluation=[0.250311],
        description="Integral approximation with \\lambda and not \\epsilon"
    ),
    TestParserData(
        solution_string="\\boxed{y(x) \\approx e^{1-x} + \\epsilon \\left(e^{1-x}(1-x) - e e^{-x/\\epsilon}\\right) + \\epsilon^2 \\left(e^{1-x}(x^2/2-3x+5/2) - \\frac{5e}{2} e^{-x/\\epsilon} - ex e^{-x/\\epsilon}\\right)}",
        parameter_string="$x;\\epsilon$",
        expected_evaluation=[-21.04819184094423],
        description="ODE solution with \\epsilon and ex implicit multiplication"
    ),
    TestParserData(
        solution_string="$\\boxed{\\frac{\sin(x\\pi) - 2\\sin(x\\pi/2)}{2\\pi x} + \\frac{4\\cos(x\\pi/2) - \\cos(x\\pi)}{2\\pi^2 x^2}}$",
        parameter_string="$x$",
        expected_evaluation=[-0.06332573977646111],
        description="ODE solution with xpi multiplication problem"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) \\approx \\frac{1}{\sqrt{\epsilon}}e^{\\frac{-x^2}{2\\epsilon}} i \\sqrt{\\frac{\\pi}{2}}erfi(\\frac{x}{\\sqrt{2\\epsilon}})+ e^{\\frac{-x^2}{2\\epsilon}}}}$",
        parameter_string="$x;\\epsilon$",
        expected_evaluation=[0.3587012320640107+0.5437934281318755j],
        description="Uniform approximation with i and erfi"
    ),
    TestParserData(
        solution_string="Some other text showing a $\\boxed{}$ environment with a \\boxed{}$ environment inside it. \\boxed{y(x) \\approx \\frac{1}{\sqrt{\epsilon}}e^{\\frac{-x^2}{2\\epsilon}} i \\sqrt{\\frac{\\pi}{2}}erfi(\\frac{x}{\\sqrt{2\\epsilon}})+ e^{\\frac{-x^2}{2\\epsilon}}}}$",
        parameter_string="$x;\\epsilon$",
        expected_evaluation=[0.3587012320640107+0.5437934281318755j],
        description="Duplicate problem with multiple \\boxed{}$ environments"
    ),
    TestParserData(
        solution_string="$\\boxed{-\\frac{3J}{4};2}$",
        parameter_string="$J$",
        expected_evaluation=[-1.0309050891355218,2],
        description="J as a parameter"
    ),
    TestParserData(
        solution_string="$\\boxed{-\\frac{3J}{4};2}$",
        parameter_string="",
        expected_evaluation=[-0.75j,2],
        description="J that should be interpreted as an imaginary number"
    ),
    TestParserData(
        solution_string="$\\boxed{\\text{a;b}}$",
        parameter_string="a;b;c",
        expected_evaluation=[1.3745401188473625, 1.9507143064099162],
        description="Text values in the solution string"
    ),
    TestParserData(
        solution_string="$$\\boxed{y = \\sin x + 2 - \\sin(1)\, \\mathrm{erf}\\left(\\frac{x}{\\sqrt{2\\epsilon}}\\right)}$$",
        parameter_string="x;\\epsilon",
        expected_evaluation=[2.195858880142043],
        description="Formula with excessive formatting for pretty latex"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x, \\epsilon)= \\exp(-M + \\int_0^x \\frac{du}{\\cosh(u)}) + (1 - e^{-M}) e^{-x/\\epsilon}}$",
        parameter_string="x;\\epsilon;M",
        expected_evaluation=[0.9455929182671768],
        description="Expression with fractional integral"
    ),
    TestParserData(
        solution_string="$\\boxed{ y(x) = \\frac{B}{1.062 e^{\\frac{9.441}{\\sqrt{\\epsilon}}}} [\\ln(\\ln(x))]^{ -1/4} e^{\\frac{1}{\\sqrt{\\epsilon}} \\int_1^x \\sqrt{\\ln t} ~ dt} + \\frac{A(1.062 e^{\\frac{9.441}{\\sqrt{\\epsilon}}}) - 1.323 B e^{\\frac{2.661}{\\sqrt{\\epsilon}}}}{1.405 e^{\\frac{6.780}{\\sqrt{\\epsilon}}}} [\\ln(\\ln(x))]^{ -1/4} e^{-\\frac{1}{\\sqrt{\\epsilon}} \\int_1^x \\sqrt{\\ln t} ~ dt} } $",
        parameter_string="x;\\epsilon;A;B",
        expected_evaluation=[(5.1870196742705-5.1870196742705j)],
        description="Complex expression with several nested integrals"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x)= |v_0|}$",
        parameter_string="v_0",
        expected_evaluation=[1.3745401188473625],
        description="Absolute value"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) \\approx \\Bigl(\\frac{\\sin 1}{\\sin x}\\Bigr)^{\\frac{1}{4}} \\Biggl( \\frac{\\sinh \\Bigl(\\frac{\\sqrt{2}}{\\epsilon}  B_{\\sin^2(\\frac{x}{2})} \\bigl(\\frac{3}{4},\\frac{3}{4}\\bigr) \\Bigr)}{ \\sinh \\Bigl(\\frac{\\sqrt{2}}{\\epsilon}  B_{\\sin^2(\\frac{1}{2})}\\bigl(\\frac{3}{4},\\frac{3}{4}\\bigr)\\Bigr)}\\Biggr)}}$",
        parameter_string="x;\\epsilon",
        expected_evaluation=[2.717213122957548],
        description="Incomplete beta function"
    ),
    TestParserData(
        solution_string="$\\boxed{\\frac{2e^{-9x}}{x} - \\frac{4e^{-9x}}{9x^2}}$",
        parameter_string="x",
        expected_evaluation=[1.3537759773077891e-08],
        description="Integral approximation solution with e^(-9x)"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = \\int_0^\\infty \\frac{e^{-t}}{t+1} dt}$",
        parameter_string="x",
        expected_evaluation=[0.5963473623231941],
        description="Integral solution with e^(-t)"
    ),
    TestParserData(
        solution_string="$\\boxed{I(x) \\approx \\int_0^1 e^{-1/t} dt - x^2 e^{-1/x}}$",
        parameter_string="x",
        expected_evaluation=[-2.2776271320746115],
        description="Integral solution with from LLM 1"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) \\approx \\frac{1}{2} \\exp\\left(\\frac{x^2-1/4}{2}\\right) \\left(1 - \\frac{2}{\\sqrt{\\pi}}\\int_0^{\\frac{x-1}{\\sqrt{2\\epsilon}}} \\exp(-t^2) dt\\right) + \\frac{1}{2} \\exp\\left(\\frac{x^2-9/4}{2}\\right) \\left(1 + \\frac{2}{\\sqrt{\\pi}}\\int_0^{\\frac{x-1}{\\sqrt{2\\epsilon}}} \\exp(-t^2) dt\\right)}$",
        parameter_string="x;\\epsilon",
        expected_evaluation=[3.3757788313551624],
        description="Integral solution with from LLM 2"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) \\approx e^{1-x} + \\epsilon \\left(e^{1-x}(1-x) - e e^{-x/\\epsilon}\\right) + \\epsilon^2 \\left(e^{1-x}(x^2/2-3x+5/2) - \\frac{5e}{2} e^{-x/\\epsilon} - ex e^{-x/\\epsilon}\\right)}$",
        parameter_string="x;\\epsilon",
        expected_evaluation=[-21.04819184094423],
        description="Integral solution with from LLM 3"
    ),
    TestParserData(
        solution_string="$\\boxed{\\frac{2}{\\sqrt{x}} - \\frac{1}{2x^{3/2}}\\int_0^{\\pi/2}\\frac{\\cos(t)\\log(1+t^2)}{\\sin^{3/2}(t)}dt + \\frac{3}{8x^{5/2}}\\int_0^{\\pi/2}\\frac{\\cos(t)(\\log(1+t^2))^2}{\\sin^{5/2}(t)}dt}$",
        parameter_string="x",
        expected_evaluation=[1.323987277272504],
        description="Integral solution with from LLM 4"
    ),
    TestParserData(
        solution_string="$\\boxed{-\\int_{0}^{1}e^{7t^5}dt + x}$",
        parameter_string="x",
        expected_evaluation=[-35.14139883093507],
        description="Integral solution with from LLM 5"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) \\approx \\left(\\frac{\\tan(0.0025)}{\\tan((x+0.25)/100)}\\right)^{1/4} \\cos\\left(\\frac{1}{\\epsilon} \\int_0^x \\sqrt{\\tan((t+0.25)/100)} dt\\right) + \\epsilon \\left(\\frac{\\tan(0.0025)}{\\tan((x+0.25)/100)}\\right)^{-1/4} \\sin\\left(\\frac{1}{\\epsilon} \\int_0^x \\sqrt{\\tan((t+0.25)/100)} dt\\right)}$",
        parameter_string="x;\\epsilon",
        expected_evaluation=[0.948304618218160],
        description="Integral solution with from LLM 6"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) \\approx x^{-1/4} \\frac{1}{4}\\Gamma(\\frac{1}{4})}$",
        parameter_string="x",
        expected_evaluation=[0.7621905937330379],
        description="Gamma function"
    ),
    TestParserData(
        solution_string="$\\boxed{-(1-x^2) - \\sqrt{(1-x^2)^2+1} + 3\\text{sech}^2\\left(\\ln(\\sqrt{3}+\\sqrt{2}) + \\frac{x+1}{\\sqrt{2\\epsilon}}\\right) + 3\\text{sech}^2\\left(\\ln(\\sqrt{3}+\\sqrt{2}) + \\frac{1-x}{\\sqrt{2\\epsilon}}\\right)}$",
        parameter_string="x;\\epsilon",
        expected_evaluation=[1.9380933179672022],
        description="Squared sech with text wrapper"
    ),
    TestParserData(
        solution_string="$\\boxed{y(x) = \\frac{\\epsilon}{(1+x)^{\\frac{1}{4}}} \\sinh\\left[\\frac{2}{3\\epsilon}(1+x)^{\\frac{3}{2}}\\right]}$",
        parameter_string="x;\\epsilon",
        expected_evaluation=[4.250811666071152],
        description="WKB approximation with error in sheet"
    ),
    TestParserData(
        solution_string="$\\boxed{u(x,t)=\\frac{1}{4}\\mathrm{sech}^2\\left(\\frac{x}{2}\\right)}$",
        parameter_string="x;t",
        expected_evaluation=[0.10499358540350652],
        description="Sech squared function inside mathrm"
    ),
    TestParserData(
        solution_string="$\\boxed{u(x,t) = \\frac{1}{4}\\operatorname{sech}^{2}\\left(\\frac{\\sqrt{3}}{4}\\left(x - \\frac{\\sqrt{10}}{2}t\\right)\\right)}$",
        parameter_string="x;t",
        expected_evaluation=[0.2020772182654035],
        description="Sech squared function inside operatorname"
    )
]