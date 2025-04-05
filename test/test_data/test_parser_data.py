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
        description="Basic boxed solution with three values"
    ),
    TestParserData(
        solution_string="$\\boxed{x;x^2;x^3}$",
        parameter_string="",
        expected_evaluation=[1,1,1],
        description="Boxed solution with polynomial expressions"
    )
]