import ctypes
import os
try:
    from sat_logic.Logic import CNF, Clause, Literal
except ModuleNotFoundError:
    from Logic import CNF, Clause, Literal

SAT = 10
UNSAT = 20


class Cadical:
    lib = ctypes.cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), "bin/ccadical.so"))
    lib.ccadical_init.argtypes = []
    lib.ccadical_init.restype = ctypes.c_void_p
    lib.ccadical_trace_proof.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ccadical_trace_proof.restype = ctypes.c_bool
    lib.ccadical_set_option.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    lib.ccadical_set_option.restype = ctypes.c_bool
    lib.ccadical_add.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.ccadical_add.restype = None
    lib.ccadical_assume.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.ccadical_assume.restype = None
    lib.ccadical_solve.argtypes = [ctypes.c_void_p]
    lib.ccadical_solve.restype = ctypes.c_int
    lib.ccadical_flush_proof_trace.argtypes = [ctypes.c_void_p]
    lib.ccadical_flush_proof_trace.restype = None
    lib.ccadical_release.argtypes = [ctypes.c_void_p]
    lib.ccadical_release.restype = None
    lib.ccadical_constrain.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.ccadical_constrain.restype = None

    def __init__(self):
        self.solver = Cadical.lib.ccadical_init()
        self.proof_filename = None

    def set_option(self, option:str, value:int) -> bool:
        return Cadical.lib.ccadical_set_option(self.solver, option.encode('utf-8'), value)
    
    def trace_proof(self, proof_filename) -> bool:
        self.proof_filename = proof_filename
        return Cadical.lib.ccadical_trace_proof(self.solver, proof_filename.encode('utf-8'))
        
    def add_literal(self, literal:Literal) -> None:
        Cadical.lib.ccadical_add(self.solver, int(literal))

    def add_clause(self, clause:Clause) -> None:
        for literal in clause:
            Cadical.lib.ccadical_add(self.solver, int(literal))
        Cadical.lib.ccadical_add(self.solver, 0)

    def add_formula(self, formula:CNF) -> None:
        for clause in formula:
            self.add_clause(clause)

    def solve(self, assumptions: list[Literal]=[], constraint: Clause = None):
        if constraint:
            for literal in constraint:
                Cadical.lib.ccadical_constrain(self.solver, int(literal))
            Cadical.lib.ccadical_constrain(self.solver, 0)

        for lit in assumptions:
            Cadical.lib.ccadical_assume(self.solver, int(lit))

        ret = Cadical.lib.ccadical_solve(self.solver)
        if ret == 20 and self.proof_filename is not None:
            Cadical.lib.ccadical_flush_proof_trace(self.solver)
        return ret
    
    def __del__(self):
        Cadical.lib.ccadical_release(self.solver)

from enum import Enum
class ProofType(Enum):
    LRAT = "lrat"
    DRAT = "drat"

class ProofSolver:
    def __init__(self, proof_name="proof.lrat", proof_type=ProofType.LRAT, proof_binary=False):
        self.solver = Cadical()
        self.solver.set_option("quiet", True)
        self.solver.set_option(proof_type.value, True)
        self.solver.set_option("binary", proof_binary)
        self.solver.trace_proof(proof_name)
        
        self.clauses = [None]

    def add_clause(self, clause):
        self.solver.add_clause(clause)
        self.clauses.append(clause)

    def add_formula(self, formula):
        for clause in formula:
            self.add_clause(clause)

    def solve(self, assumptions: list[int] = [], constraint: Clause = None):
        self.last_assumptions = assumptions
        self.last_constraint = constraint

        ret = self.solver.solve(assumptions, constraint)
        # if assumptions or constraints are used, the proof doesn't end with 0
        # we have to finish with the last clause
        return ret

    @staticmethod
    def implies(hypothesis, conclusion):
        # (hypothesis -> conclusion) == ~hypothesis | conclusion == ~(hypothesis & ~conclusion)
        solver = Cadical()
        solver.add_formula(hypothesis)
        solver.add_formula(~conclusion)
        return solver.solve() == UNSAT


if __name__ == "__main__":
    solver = ProofSolver()
    
    solver.add_formula(CNF([[2,3], [2,-3],[-2,3],[-2,-3]]))
    solver.solve()
    '''
    solver.add_formula(CNF([-2, -3, 4], [-2,-3,-4]))
    solver.solve(assumptions=[2,3])
    '''
    

