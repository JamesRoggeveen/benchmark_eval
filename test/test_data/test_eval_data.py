from typing import Optional
from dataclasses import dataclass

@dataclass
class TestEvalData:
    input: str
    solution: str
    parameters: str
    model: str
    enabled: bool = True
    functions: Optional[str] = ""
    description: Optional[str] = None

test_data = [
    TestEvalData(
        input="Consider the following equation: $y^2 y'' = 1+x$. In the limit $x\\rightarrow +\\infty$, find all approximate behaviors of $y$ including the leading non-zero order in x. Provide your answer in a $\\boxed{}$ latex environment and separate all potential solutions with a ;",
        solution="$\\boxed{y(x) = 3^{\\frac{1}{3}}x (\\ln x)^{\\frac{1}{3}}}$",
        parameters="$x$",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Differential equation limit behavior"
    ),
    TestEvalData(
        input="Find the value of x if 2x + 3 = 7. Use only the variables and constants given in the problem; do not define additional constants. Place your final solution in a $\\boxed{}$ LaTeX environment.",
        solution="$\\boxed{x = 2}$",
        parameters="$x$",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Simple linear equation"
    ),
    TestEvalData(
        input="A doublet of strength $m$ is situated at the centre of a sphere of radius $a$. Find the radial $u$ and transversal $v$ velocities of the liquid in terms of $m$ and $a$ as a function of the spherical coordinates $r$, $\\theta$, and $\\psi$. Use only the variables and constants given in the problem; do not define additional constants. If necessary, numerical approximations are fine. Place your final solution in a $\\boxed{}$ LaTeX environment with all components of the solution separated by a semicolon ;.",
        solution="$\\boxed{u = m\\left(\\frac{2}{r^3} - \\frac{5}{a^3} + \\frac{3r^2}{a^5}\\right)\\cos \\theta; v = m\\left(\\frac{1}{r^3}+\\frac{5}{a^3}-\\frac{6r^2}{a^5}\\right)\\sin \\theta}$",
        parameters="$m; r; \\theta; a; \\psi$",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Fluid dynamics with spherical coordinates"
    ),
    TestEvalData(
        input="Find a uniformly valid approximation to the solution of $\\epsilon y'' - x y' + x^3 y = 0$ with boundary conditions $y(0) = 1$, $y(1) = 2$ in the limit $\\epsilon \\ll 1$. Use only the variables and constants given in the problem; do not define additional constants. If necessary, numerical approximations are fine. Place your final solution in a $\\boxed{}$ LaTeX environment.",
        solution="$\\boxed{y = e^{\\frac{x^3}{3}} + (2-e^{1/3})e^{-(1-x)/\\epsilon}}$",
        parameters="$x;\\epsilon$",
        model="Gemini 2.0 Flash Thinking",
        enabled=True,
        description="Singular perturbation problem"
    ),
    TestEvalData(
        input="We are interested in solving the self-consistency equation for Hartree-Fock mean-field theory on a 2D triangular lattice associated with the following mean-field Hamiltonian $H = H_{\\text{Kinetic}} + H_{\\text{Hartree}} +H_{\\text{Fock}}$, with $H_{\\text{Kinetic}} = \\sum_{s, k} E_s(k) c^\\dagger_s(k) c_s(k)$, where $E_s(k)=\\sum_{n} t_s(n) e^{-i k \\cdot n}$ with the spin index $s = \\{\\uparrow, \\downarrow\\}$ and momentum $k$. The mean-field terms are $H_{\\text{Hartree}} = \\frac{1}{N} \\sum_{s, s'} \\sum_{k_1, k_2} U(0) \\langle c_s^\\dagger(k_1) c_s(k_1) \\rangle c_{s'}^\\dagger(k_2) c_{s'}(k_2)$ $H_{\\text{Fock}} = -\\frac{1}{N} \\sum_{s, s'} \\sum_{k_1, k_2} U(k_1 - k_2) \\langle c_s^\\dagger(k_1) c_{s'}(k_1) \\rangle c_{s'}^\\dagger(k_2) c_s(k_2)$, where $U(k) = \\sum_{n} U_n e^{-i k \\cdot n}$ is the interaction strength in the momentum basis. What would be the dimension of the matrix associated with each momentum $k$ that should be diagonalized, if you are to solve the self-consistency equation numerically? Print your answer in numbers.  Please render your answer in LaTeX format and place your final solution in a $\\boxed{}$ LaTeX environment. There should only be one $\\boxed{}$ environment.",
        solution="$\\boxed{2}$",
        parameters="",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Hartree-Fock mean-field theory matrix dimension"
    ),
    TestEvalData(
        input="Consider a two-dimensional triangular lattice with a mean-field Hamiltonian described in momentum space. The Brillouin zone of this lattice forms a hexagon, where two corners are on the $k_y$ axis. What are the coordinates of the six Brillouin zone corners ($K$ and $K'$ points) for this lattice structure? Round your answers to 2 decimal places. Place your final solution in a $\\boxed{}$ LaTeX environment with each coordinate in the form (x,y) separated by a semicolon ;",
        solution="$\\boxed{(0,  4.19);(0, -4.19);(3.63, 2.09);(-3.63, 2.09);(3.63, -2.09);(-3.63, -2.09)}$",
        parameters="",
        model="Gemini 2.0 Flash Thinking",
        enabled=True,
        description="Triangular lattice Brillouin zone corners"
    ),
    TestEvalData(
        input="Consider a two-dimensional triangular lattice described by a mean-field Hamiltonian in momentum space. What are the coordinates of the Brillouin zone center ($\\Gamma$ point) for this lattice structure? Round your answers to 2 decimal places. Place your final solution in a $\\boxed{}$ LaTeX environment with the coordinates in the form (x,y) separated by a semicolon ;",
        solution="$\\boxed{(0,0)}$",
        parameters="",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Triangular lattice Brillouin zone center"
    ),
    TestEvalData(
        input="Consider a two-dimensional triangular lattice with a noninteracting band structure. The system can be described by the kinetic term of the following Hamiltonian: $H_{\\text{Kinetic}} = \\sum_{s, k} E_s(k) c^\\dagger_s(k) c_s(k)$, where $E_s(k)=\\sum_{n} t_s(n) e^{-i k \\cdot n}$. The hopping parameters are $t_1 = 6$ meV for nearest-neighbor hopping and $t_2 = 1$ meV for next-nearest-neighbor hopping, which correspond to $t_s(n)$ in the kinetic energy term. The spin index $s$ takes values in $\\{\\uparrow, \\downarrow\\}$. What are the energies at the center of the Brillouin zone ($\\Gamma$ point) for all bands in this system? Print your answer in the unit of meV within a $\\boxed{}$ LaTeX environment with each energy separated by a ;. Your answer should only contain one $\\boxed{}$ environment.",
        solution="$\\boxed{48; 48}$",
        parameters="",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Triangular lattice band energies at Gamma point"
    ),
    TestEvalData(
        input="We are interested in solving the self-consistency equation for Hartree-Fock mean-field theory on a 2D triangular lattice associated with the following mean-field Hamiltonian $H = H_{\\text{Kinetic}} + H_{\\text{Hartree}} +H_{\\text{Fock}}$, with $H_{\\text{Kinetic}} = \\sum_{s, k} E_s(k) c^\\dagger_s(k) c_s(k)$, where $E_s(k)=\\sum_{n} t_s(n) e^{-i k \\cdot n}$ with the spin index $s = \\{\\uparrow, \\downarrow\\}$ and momentum $k$. The mean-field terms are $H_{\\text{Hartree}} = \\frac{1}{N} \\sum_{s, s'} \\sum_{k_1, k_2} U(0) \\langle c_s^\\dagger(k_1) c_s(k_1) \\rangle c_{s'}^\\dagger(k_2) c_{s'}(k_2)$ $H_{\\text{Fock}} = -\\frac{1}{N} \\sum_{s, s'} \\sum_{k_1, k_2} U(k_1 - k_2) \\langle c_s^\\dagger(k_1) c_{s'}(k_1) \\rangle c_{s'}^\\dagger(k_2) c_s(k_2)$, where $U(k) = \\sum_{n} U_n e^{-i k \\cdot n}$ is the repulsive interaction strength ($U_n>0$) in the momentum basis. What are the possible order parameters that preserve translational symmetry for a Hartree-Fock mean-field Hamiltonian on a two-dimensional triangular lattice?  Give all valid order parameters separate by a ; within a single $\\boxed{}$ environment. Print your answer using only the operators provided.",
        solution="\\boxed{\\langle c_\\uparrow^\\dagger(k) c_\\uparrow(k) \\rangle; \\langle c_\\downarrow^\\dagger(k) c_\\downarrow(k) \\rangle}",
        parameters="$k; N$",
        functions="$(c_s^\\dagger, NC); (c_s, NC), (s,\\uparrow,\\downarrow)$",
        model="Gemini 2.0 Flash Thinking",
        enabled=True,
        description="Triangular lattice order parameters"
    ),
    TestEvalData(
        input="What is the kinetic term of the real-sapce Hamiltonian in second-quantized form for a triangular lattice system with spin states associated with +K and -K valleys? Consider a triangular lattice system where the degrees of freedom are spin states associated with +K and -K valleys. In this system, electrons can hop between sites with amplitude $t_s(R_i - R_j)$. The spin states $s = \\uparrow,\\downarrow$ represent states associated with +K and -K valleys, respectively. Each site in the triangular lattice is located at position $R_i$. The electron annihilation operator at site with position $R_i$ with spin $s$ is denoted by $c_{R_i,s}$, while the electron creation operator at the same site with the same spin is denoted by $c^{\\dagger}_{R_i,s}$. The hopping process occurs between sites at positions $R_i$ and $R_j$. Derive the complete tight-binding Hamiltonian $H_{TB}$ for this system. You should find that the hamitolian consists of a function summed over the latice grid, : $H_{TB} = -\\sum_{R_i,R_j} f$. Return the function f in a $\\boxed{}$ LaTeX environment.",
        solution="\\boxed{f = t_{\\uparrow}(R_i - R_j) c_{R_i,\\uparrow}^{\\dagger} c_{R_j,\\uparrow} + t_{\\downarrow}(R_i - R_j) c_{R_i,\\downarrow}^{\\dagger} c_{R_j,\\downarrow}}",
        functions="$t_n; (n,\\uparrow,\\downarrow)$",
        parameters="$R_i; R_j, (c_{m,n}^{\\dagger}, NC); (c_{m,n}, NC);(m,R_i,R_j);(n,\\uparrow,\\downarrow)$",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Triangular lattice tight-binding Hamiltonian"
    ),
    TestEvalData(
        input="Consider a triangular lattice system with spin degrees of freedom associated with $+K$ and $-K$ valleys. The spin states $s = \\uparrow,\\downarrow$ represent states associated with +K and -K valleys, respectively. The system features density-density interactions between sites at positions $R_i$ and $R_j$ with interaction strength $U(R_i - R_j)$. The electron annihilation operator at site $R_i$ with spin $s$ is denoted by $c_{R_i,s}$, while the corresponding creation operator is denoted by $c^{\\dagger}_{R_i,s}$. The number operator for electrons with spin $s$ at site position $R_i$ is defined as $n_s(R_i) = c^{\\dagger}_{R_i,s}c_{R_i,s}$. Derive the interaction Hamiltonian $H^{\\text{int}}$, which will take the form of $H^{\\text{int}} = \\sum_{R_i,R_j} f$. Return the function $f$ as your solution in therms of the interation strength $U$ and the number operator $n$. Do not use any summation notation in your answer and place it in a $\\boxed{}$ latex environment",
        solution="\\boxed{f = U(R_i - R_j) (n_{\\uparrow}(R_i) + n_{\\downarrow}(R_i)) (n_{\\uparrow}(R_j) + n_{\\downarrow}(R_j))}",
        functions="$U; n_{\\uparrow}; n_{\\downarrow}$",
        parameters="$R_i; R_j$",
        model="Gemini 2.0 Flash Thinking",
        enabled=False,
        description="Triangular lattice interaction Hamiltonian"
    )
]

def get_enabled_tests():
    """Returns only the enabled test cases"""
    return [test for test in test_data if test.enabled]

def to_json(test_case: TestEvalData) -> dict:
    """Convert a TestEvalData instance to the JSON format expected by the API"""
    return {
        "input": test_case.input,
        "solution": test_case.solution,
        "parameters": test_case.parameters,
        "functions": test_case.functions,
        "model": test_case.model
    } 