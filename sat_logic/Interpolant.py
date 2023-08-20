try:
    from sat_logic.ColoredLogic import ColorfulCNF
    from sat_logic.Logic import CNF, Clause
    from sat_logic.Solvers import ProofSolver, SAT
except ModuleNotFoundError:
    from ColoredLogic import ColorfulCNF
    from Logic import CNF, Clause
    from Solvers import ProofSolver, SAT

class SATException(Exception):
    pass

class LabeledClause:
    def __init__(self, clause: Clause, label: CNF, index: int) -> None:
        self.clause = clause
        self.label = label
        self.index = index
        self.parents = []

class ProofClause(LabeledClause):
    def __init__(self, line: str) -> None:
        parts = line.split()
        self.index = int(parts[0])
        self.parents = [int(lit) for lit in parts[parts.index("0")+1:-1]]
        self.clause = Clause({int(lit) for lit in parts[1:parts.index("0")]})
        self.label = None

class Interpolant:
    def __init__(self, colorful_cnf: ColorfulCNF) -> None:
        self.colorful_cnf = colorful_cnf
        self.proof_clauses = list(colorful_cnf)
        self.proof_clauses.insert(0, Clause(1)) # Constant true
        self.color_variables = colorful_cnf.color[1].variables

        self.solver = ProofSolver()
        self.solver.add_formula(self.proof_clauses)
        if self.solver.solve() == SAT:
            raise SATException("Formula is SAT")
        self.proof_clauses.insert(0, Clause())  # Shift the clauses by 1

        with open("proof.lrat", "r") as proof_file:
            for line in proof_file:
                if line.split()[1] != "d":
                    self.last_step = ProofClause(line)
                    self.proof_clauses.insert(self.last_step.index, self.last_step)
                    self.proof_clauses[self.last_step.index].label = self.getLabel(self.last_step.index)

    @property
    def cnf(self):
        return self.last_step.label

    def getLabel(self, index):
        clause = self.proof_clauses[index]
        if not isinstance(clause, LabeledClause):
            label = None
            if clause in self.colorful_cnf.color[1]:
                label = CNF([Clause({1})], keep_minimal=True)
            else:
                label = CNF({clause.intersection(
                    self.color_variables)}, keep_minimal=True)
            self.proof_clauses[index] = LabeledClause(clause, label, index)
            return label

        if clause.label is not None:
            return clause.label
        
        parents = clause.parents

        label = self.getLabel(parents[-1])
        clause = self.proof_clauses[parents[-1]].clause

        for i in range(len(parents) - 2, -1, -1):
            parent_label = self.getLabel(parents[i])
            parent_clause = self.proof_clauses[parents[i]].clause
            resolvant = clause.resolvant(parent_clause)
            clause = clause.resolve_on(parent_clause, resolvant)
            if resolvant not in self.color_variables:
                label = label | parent_label
            else:
                label = label & parent_label
        self.proof_clauses[index].label = label
        return label


if __name__ == "__main__":
    # Test case taken from the book with a = 2, b = 3, ...
    ccnf = ColorfulCNF(
        [CNF([[-2, 5], [-2, 3, -5], [-2, -3], [2, -3], [2, 3, 5]]), CNF([[3, -5]])])
    interpolant = Interpolant(ccnf)
    clauses = interpolant.cnf
    if Clause({-3}) in clauses and Clause({5}) in clauses and len(clauses) == 2:
        print("Interpolant [PASS]")
    else:
        print("Interpolant [FAIL]")
        print(f'Expected: (¬3) ∧ (5)')
        print(f'Actual:   {clauses}')
