from sat_logic.ColoredLogic import ColorfulCNF
from sat_logic.Logic import CNF, Clause
from sat_logic.Solvers import ProofSolver

class LabeledClause:
    def __init__(self, clause: Clause, label:CNF, index:int) -> None:
        self.clause = clause
        self.label = label
        self.index = index
        self.parents = []
    
    def derivesEmpty(self) -> bool:
        return self.clause.isUnsat
    
    def __hash__(self) -> int:
        return hash(self.index)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            return self.index == other
        return self.index == other.index


class ProofClause(LabeledClause):
    def __init__(self, line: str) -> None:
        parts = line.split()
        self.index = int(parts[0])
        self.parents = [int(lit) for lit in parts[parts.index("0")+1:-1]]
        self.clause = Clause({int(lit) for lit in parts[1:parts.index("0")]})
        self.label = None
        

class Interpolant:
    def __init__(self, prooffile:str, colorful_cnf:ColorfulCNF, assumptions=[]) -> None:
        self.colorful_cnf = colorful_cnf
        self.cnf_clauses = list(colorful_cnf)
        self.cnf_clauses.insert(0, Clause()) # Shift the clauses by 1
        self.cnf_clauses.insert(1, Clause({1})) # Add the constant true symbol
        self.color_variables = colorful_cnf.color[1].variables

        self.solver = ProofSolver()
        self.solver.add_formula(colorful_cnf)
        self.solver.solve()

        self.proof = dict()
        with open(prooffile, "r") as proof_file:
            for line in proof_file:
                if line.split()[1] != "d":
                    proof_clause = ProofClause(line)
                    self.last_index = proof_clause.index
                    self.proof[self.last_index] = proof_clause

    @property
    def cnf(self):
        return self.getLabeledClause(self.last_index).label
    
    def getLabeledClause(self, index):
        if index not in self.proof: # Root clause
            clause = self.cnf_clauses[index]
            label = None
            if clause in self.colorful_cnf.color[1]:
                label = CNF([Clause({1})], keep_minimal=True)
            else:
                label = CNF({clause.intersection(self.colorful_cnf.color[1].variables)}, keep_minimal=True)
            self.proof[index] = LabeledClause(clause, label, index)
            return self.proof[index]
        
        current_labeled_clause = self.proof[index]
        label = current_labeled_clause.label
        if label:
            return current_labeled_clause
        
        parents = current_labeled_clause.parents

        labeled_clause = self.getLabeledClause(parents[-1])
        label = labeled_clause.label
        derived_clause = labeled_clause.clause

        for i in range(len(parents) - 2, -1, -1):
            labeled_clause = self.getLabeledClause(parents[i])
            clause = labeled_clause.clause
            resolvant = derived_clause.resolvant(clause)
            print(f"resolving {derived_clause} with {clause} on {resolvant}")
            derived_clause = derived_clause.resolve_on(clause, resolvant)
            if resolvant not in self.color_variables:
                label = label | labeled_clause.label
            else: 
                label = label & labeled_clause.label
        labeled_clause = LabeledClause(derived_clause, label, index)
        self.proof[index] = labeled_clause
        return labeled_clause


if __name__ == "__main__":
    from Logic import Clause
    # Test case taken from the book with a = 2, b = 3, ...
    ccnf = ColorfulCNF([CNF([[-2, 5], [-2, 3, -5], [-2, -3], [2, -3], [2, 3, 5]]), CNF([[3, -5]])])
    print(list(ccnf))
    interpolant = Interpolant("proof.lrat", ccnf)
    clauses = interpolant.cnf
    if Clause({-3}) in clauses and Clause({5}) in clauses and len(clauses) == 2:
        print("Interpolant [PASS]")
    else:
        print("Interpolant [FAIL]")
        print(f'Expected: (¬3) ∧ (5)')
        print(f'Actual:   {clauses}')
