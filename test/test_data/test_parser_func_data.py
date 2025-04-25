from typing import List, Optional
from dataclasses import dataclass

@dataclass
class TestParserFuncData:
    comparison_string:str
    solution_string:str
    parameter_string:str
    function_string:str
    expected_result:bool
    description: Optional[str] = None

test_data = [
    TestParserFuncData(
        comparison_string="\\boxed{\\langle c_\\downarrow^\\dagger(k) c_\\downarrow(k) \\rangle; \\langle c_\\uparrow^\\dagger(k) c_\\uparrow(k) \\rangle}",
        solution_string="\\boxed{\\langle c_\\uparrow^\\dagger(k) c_\\uparrow(k) \\rangle; \\langle c_\\downarrow^\\dagger(k) c_\\downarrow(k) \\rangle}",
        parameter_string="$k$",
        function_string="$(c_s^\\dagger, NC); (c_s, NC), (s,\\uparrow,\\downarrow)$",
        expected_result=True,
        description="Non commuting operators with NC-flags, and different order of terms"),
    TestParserFuncData(
        comparison_string="\\boxed{\\langle c_\\uparrow(k) c_\\uparrow^\\dagger(k) \\rangle; \\langle c_\\downarrow^\\dagger(k) c_\\downarrow(k) \\rangle}",
        solution_string="\\boxed{\\langle c_\\uparrow^\\dagger(k) c_\\uparrow(k) \\rangle; \\langle c_\\downarrow^\\dagger(k) c_\\downarrow(k) \\rangle}",
        parameter_string="$k$",
        function_string="$(c_s^\\dagger, NC); (c_s, NC), (s,\\uparrow,\\downarrow)$",
        expected_result=False,
        description="Non commuting operators with NC-flags, and commuted terms"),
    TestParserFuncData(
        comparison_string="\\boxed{\\langle c_\\uparrow^\\dagger(k) c_\\downarrow(k) \\rangle; \\langle c_\\downarrow^\\dagger(k) c_\\downarrow(k) \\rangle}",
        solution_string="\\boxed{\\langle c_\\uparrow^\\dagger(k) c_\\uparrow(k) \\rangle; \\langle c_\\downarrow^\\dagger(k) c_\\downarrow(k) \\rangle}",
        parameter_string="$k$",
        function_string="$(c_s^\\dagger, NC); (c_s, NC), (s,\\uparrow,\\downarrow)$",
        expected_result=False,
        description="Non commuting operators with NC-flags, and different terms"),
    TestParserFuncData(
        comparison_string="\\boxed{f=U(R_i - R_j) (n_{\\uparrow}(R_i) + n_{\\downarrow}(R_i)) (n_{\\uparrow}(R_j) + n_{\\downarrow}(R_j))}",
        solution_string="\\boxed{f=U(R_i - R_j) (n_{\\uparrow}(R_i) + n_{\\downarrow}(R_i)) (n_{\\uparrow}(R_j) + n_{\\downarrow}(R_j))}",
        function_string="$U; n_{\\uparrow}; n_{\\downarrow}$",
        parameter_string="$R_i; R_j$",
        expected_result=True,
        description="Algebraic expression with multiple equivalent terms"),
    TestParserFuncData(
        comparison_string="\\boxed{f=U(R_i - R_j) (n_{\\uparrow}(R_i) + n_{\\downarrow}(R_i)) (n_{\\uparrow}(R_j) + n_{\\downarrow}(R_j))}",
        solution_string="\\boxed{f=U(R_i - R_j) (n_{\\uparrow}(R_i)) (n_{\\uparrow}(R_j) + n_{\\downarrow}(R_j))}",
        function_string="$U; n_{\\uparrow}; n_{\\downarrow}$",
        parameter_string="$R_i; R_j$",
        expected_result=False,
        description="Algebraic expression with non-equivalent terms"),
    TestParserFuncData(
        comparison_string="\\boxed{f = t_{\\uparrow}(R_i - R_j) c_{R_i,\\uparrow}^{\\dagger} c_{R_j,\\uparrow} + t_{\\downarrow}(R_i - R_j) c_{R_i,\\downarrow}^{\\dagger} c_{R_j,\\downarrow}}",
        solution_string="\\boxed{f = t_{\\uparrow}(R_i - R_j) c_{R_i,\\uparrow}^{\\dagger} c_{R_j,\\uparrow} + t_{\\downarrow}(R_i - R_j) c_{R_i,\\downarrow}^{\\dagger} c_{R_j,\\downarrow}}",
        function_string="$t_n; (n,\\uparrow,\\downarrow)$",
        parameter_string="$R_i; R_j, (c_{m,n}^{\\dagger}, NC); (c_{m,n}, NC);(m,R_i,R_j);(n,\\uparrow,\\downarrow)$",
        expected_result=True,
        description="Algebraic expression with multiple non-commuting operators and regular operators"),
    TestParserFuncData(
        comparison_string="\\boxed{f = c_{R_i,\\uparrow}^{\\dagger} c_{R_j,\\uparrow} t_{\\uparrow}(R_i - R_j) + c_{R_i,\\downarrow}^{\\dagger} c_{R_j,\\downarrow} t_{\\downarrow}(R_i - R_j)}",
        solution_string="\\boxed{f = t_{\\uparrow}(R_i - R_j) c_{R_i,\\uparrow}^{\\dagger} c_{R_j,\\uparrow} + t_{\\downarrow}(R_i - R_j) c_{R_i,\\downarrow}^{\\dagger} c_{R_j,\\downarrow}}",
        function_string="$t_n; (n,\\uparrow,\\downarrow)$",
        parameter_string="$R_i; R_j, (c_{m,n}^{\\dagger}, NC); (c_{m,n}, NC);(m,R_i,R_j);(n,\\uparrow,\\downarrow)$",
        expected_result=True,
        description="Algebraic expression with multiple non-commuting operators and regular operators with order of commuting terms switched"),
    TestParserFuncData(
        comparison_string="\\boxed{f = c_{R_i,\\uparrow}^{\\dagger} c_{R_j,\\uparrow} t_{\\uparrow}(R_i - R_j) + c_{R_i,\\downarrow}^{\\dagger} c_{R_j,\\downarrow} t_{\\downarrow}(R_i - R_j)}",
        solution_string="\\boxed{f = t_{\\uparrow}(R_i - R_j) c_{R_j,\\uparrow} c_{R_i,\\uparrow}^{\\dagger} + t_{\\downarrow}(R_i - R_j) c_{R_j,\\downarrow} c_{R_i,\\downarrow}^{\\dagger}}",
        function_string="$t_n; (n,\\uparrow,\\downarrow)$",
        parameter_string="$R_i; R_j, (c_{m,n}^{\\dagger}, NC); (c_{m,n}, NC);(m,R_i,R_j);(n,\\uparrow,\\downarrow)$",
        expected_result=False,
        description="Algebraic expression with multiple non-commuting operators and regular operators with order of non-commuting terms switched")
]
