from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.linalg import solve, lstsq, LinAlgError
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class System:
    """
    A class to hold data representing a system to find a solution for.
    """

    variables: np.ndarray[tuple[int, int], np.float64]
    targets: np.ndarray[tuple[int], np.float64]


@dataclass(frozen=True)
class Constraints:
    """
    A class to hold data representing constraints to limit solutions to.
    """

    integrality: np.ndarray[tuple[int], np.bool]
    minimization: np.ndarray[tuple[int], np.bool]
    maximization: np.ndarray[tuple[int], np.bool]
    lower_bounds: np.ndarray[tuple[int], np.float64]
    upper_bounds: np.ndarray[tuple[int], np.float64]


@dataclass(frozen=True)
class _Solution:
    """
    A class to hold data representing a found solution with a descriptor message.
    """

    message: str
    array: np.ndarray[tuple[int], np.float64] | None = None


solution_message = {0: "Optimal solution found:",
                    1: "Solution took too long to find.",
                    2: "No feasible solution.",
                    3: "Unbounded solution space."}


def _analyze_system(system: System) -> tuple[float, bool]:
    """
    Analyzes the system to determine how many solutions it has. If there is exactly 1 solution, the
    system will also be checked for being square in order to use a better-suited algorithm for
    solving.

    :param system: The system to analyze
    :return: A tuple with the first element being the number of possible solutions and the second
        element being a boolean representation of the system being square
    """

    variable_rank = np.linalg.matrix_rank(system.variables)
    system_rank = np.linalg.matrix_rank(np.column_stack([system.variables, system.targets]))

    if variable_rank != system_rank:
        return 0, False
    elif variable_rank == system.variables.shape[1]:
        return 1, system.variables.shape[0] == system.variables.shape[1]
    else:
        return np.inf, False


def _constrained_solution(system: System, constraints: Constraints) -> _Solution:
    """
    Returns the solution to the provided system which solution space has infinite solutions.
    The solution is constrained using the provided argument. If a solution can not be found, a
    relevant error message is returned instead.

    :param system: The system to find a solution for
    :param constraints: The constraints to apply on the solution
    :return: The found solution with a descriptor message or an error message
    """

    objective = np.zeros(system.variables.shape[1], dtype=np.int8)
    objective[constraints.minimization] = 1
    objective[constraints.maximization] = -1

    result = milp(
        objective,
        integrality=constraints.integrality.astype(np.uint8),
        bounds=Bounds(constraints.lower_bounds, constraints.upper_bounds),
        constraints=LinearConstraint(system.variables, system.targets, system.targets)
    )

    return _Solution(solution_message.get(result.status, result.message),
                     result.x if not result.status else None)


def get_solution(system: System, constraints: Constraints) -> _Solution:
    """
    Returns the solution to the provided system. The solution is constrained using the provided
    argument if the solution-space is infinite. If a solution cannot be found or an unexpected error
    occurs, a relevant descriptor message is returned instead.

    :param system: The system to find a solution for
    :param constraints: The constraints to apply on the solution
    :return: The found solution, or None if no solution, with a relevant descriptor message
    """

    num_solutions, is_square = _analyze_system(system)

    if num_solutions == 0:
        return _Solution("No feasible solution.")
    elif num_solutions == 1:
        try:
            if is_square:
                array = solve(system.variables, system.targets)
            else:
                array, *_ = lstsq(system.variables, system.targets)
        except LinAlgError as e:
            return _Solution("Unexpected error when trying to find the solution: " + str(e))
        else:
            return _Solution("Unique solution found (no constraints applied):", array)
    else:
        return _constrained_solution(system, constraints)