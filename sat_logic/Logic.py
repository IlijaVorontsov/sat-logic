class Literal:
    def __init__(self, literal:int):
        assert literal != 0
        self.literal = literal

    @property
    def variable(self):
        return abs(self.literal)
    
    @property
    def polarity(self):
        return 1 if self.literal > 0 else -1

    def __invert__(self):
        return Literal(-self.literal)
    
    def __str__(self):
        if self.literal == 1:
            return "⊤"
        elif self.literal == -1:
            return "⊥"
        return f"¬{self.variable}" if self.polarity == -1 else str(self.variable)
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def isTrue(self):
        return self.literal == 1
    
    @property
    def isFalse(self):
        return self.literal == -1
    
    def __eq__(self, other):
        assert type(other) in [int, Literal]
        if type(other) == int:
            other = Literal(other)
        return self.literal == other.literal
    
    def __hash__(self):
        return hash(self.literal)
    
    def __int__(self):
        return self.literal

true = Literal(1)
false = Literal(-1)

class Clause:
    def __init__(self, literals=-1):
        assert type(literals) in [set, list, int, Literal]
        if type(literals) in [int, Literal]:
            literals = {literals}
        
        self.max_var = 1
        self.literals = set()

        for literal in literals:
            if type(literal) == int:
                literal = Literal(literal)

            if literal.isTrue:
                self.literals = {literal}
                break
             
            elif not literal.isFalse:
                self.literals.add(literal)
                self.max_var = max(self.max_var, literal.variable)

        for literal in self.literals:
                if ~literal in self.literals:
                    self.literals = {true}
                    return
                
        if self.literals == set():
            self.literals = {false}
        
    @property
    def variables(self):
        vars = set()
        for literal in self.literals:
            vars.add(literal)
            vars.add(~literal)
        return vars

    @property
    def isValid(self):
        return self.literals == {true}
    
    @property
    def isUnsat(self):
        return self.literals == {false}
    
    def __invert__(self):
        if self.isValid:
            return CNF({set()})
        if self.isUnsat:
            return CNF(set())
        return CNF({Clause([~literal]) for literal in self.literals})
    
    def __or__(self, other):
        assert type(other) in [Clause, Literal, int]
        if type(other) in [Literal, int]:
            other = Clause([other])
        return Clause(self.literals.union(other.literals))
    
    def __and__(self, other):
        return CNF({self, other})
    
    def __str__(self):
        return " ∨ ".join(str(literal) for literal in self.literals)
    
    def __repr__(self):
        return self.__str__()
    
    def __iter__(self):
        return iter(self.literals)
    
    def resolvant(self, other) -> int:
        possible = 0
        for literal in self.literals:
            if ~literal in other.literals:
                if possible != 0:
                    return 0
                possible = literal.variable
        return possible

    def resolve_on(self, other, resolvant):
        if resolvant == 0:
            return None
        else:
            new = set()
            for literal in self.literals:
                if literal.variable != resolvant:
                    new.add(literal)
            for literal in other.literals:
                if literal.variable != resolvant:
                    new.add(literal)
            return Clause(new)
    
    def intersection(self, other: set[int]):
        return Clause(self.literals.intersection(other))
    
    def distributeUnits(self, units):
        new = set()
        for literal in self.literals:
            if literal in units:
                return Clause({1})
            elif ~literal not in units:
                new.add(literal)
        return Clause(new)
    
    def implies(self, other) -> bool:
        assert type(other) == Clause
        return self.literals.issubset(other.literals)
    
    def __len__(self):
        return len(self.literals)
    
    @property
    def unitLiteral(self) -> Literal:
        if len(self.literals) != 1:
            return None
        return list(self.literals)[0]
    
    def __eq__(self, other):
        assert isinstance(other, Clause)
        return self.literals == other.literals
    
    def __hash__(self) -> int:
        return hash(tuple(self.literals))

class CNF:
    def __init__(self, clauses=set(), keep_minimal=False):
        assert type(clauses) in [set, list, Clause, Literal, int, CNF]
        self.keep_minimal = keep_minimal

        if type(clauses) not in [set, list]:
            clauses = {clauses}

        self.clauses = set()
        for clause in clauses:
            if type(clause) != Clause:
                clause = Clause(clause)
            if clause.isUnsat:
                self.clauses = {Clause()}
                return
            if not clause.isValid:
                self.clauses.add(clause)

        if keep_minimal:
            self.distributeUnits()
            self.removeImplied()

    def removeImplied(self):
        new_clauses = set()
        for clause1 in self.clauses:
            implied = False
            for clause2 in self.clauses:
                if clause1 is not clause2 and clause2.implies(clause1):
                    implied = True
                    break
            if not implied:
                new_clauses.add(clause1)
        self.clauses = new_clauses

    @property
    def isTrivialValid(self):
        return len(self.clauses) == 0
    
    @property
    def isTrivialUnsat(self):
        if len(self.clauses) > 1:
            return False
        return list(self.clauses)[0].isUnsat
    
    def __iter__(self):
        return iter(self.clauses)
    
    def __str__(self):
        if self.isTrivialValid:
            return "⊤"
        return " ∧ ".join("(" + str(clause) + ")" for clause in self.clauses)
    
    def __repr__(self):
        return self.__str__()
    
    def __and__(self, other):
        if isinstance(other, Clause):
            other = CNF({other})
        return CNF(self.clauses.union(other.clauses), keep_minimal=self.keep_minimal)
    
    def __or__(self, other):
        return CNF({clause1 | clause2 for clause1 in self.clauses for clause2 in other.clauses}, keep_minimal=self.keep_minimal)

    def __invert__(self):
        CNFs = [~clause for clause in self.clauses] 
        result = CNF(Clause(), keep_minimal=self.keep_minimal)
        for c in CNFs:
            result = result | c
        return result
    
    def __len__(self):
        return len(self.clauses)
    
    def __iter__(self):
        return iter(self.clauses)
    
    def distributeUnits(self):
        unit_literals = set()
        new_clauses = set()
        new_unit_literals = self.findUnitLiterals()
        
        while len(new_unit_literals) > 0:
            unit_literals.update(new_unit_literals)

            for unit_literal in new_unit_literals:
                if ~unit_literal in unit_literals:
                    self.clauses = {Clause([])}
                    return

            for clause in self.clauses:
                new_clause = clause.distributeUnits(new_unit_literals)
                if not new_clause.isValid and not new_clause.isUnsat:
                    new_clauses.add(new_clause)
                elif new_clause.isUnsat:
                    self.clauses = {Clause([])}
                    return
                # else trivial

            self.clauses = new_clauses
            new_clauses = set()

            new_unit_literals = self.findUnitLiterals()
            

        self.clauses.update({Clause([unit_literal]) for unit_literal in unit_literals})

    def findUnitLiterals(self):
        unit_clauses = set()
        for clause in self.clauses:
            literal = clause.unitLiteral
            if literal is not None:
                unit_clauses.add(literal)
        return unit_clauses
    
    @property
    def variables(self) -> set[int]:
        vars = set()
        for clause in self.clauses:
            vars.update(clause.variables)
        return vars
    
    def implies(self, other):
        for clause in other.clauses:
            if not self.implies_clause(clause):
                return False
        return True

    def implies_clause(self, clause):
        for c in self.clauses:
            if c.implies(clause):
                return True
        return False
    
    def __eq__(self, other):
        assert isinstance(other, CNF)
        return self.clauses == other.clauses
        
if __name__ == "__main__":
    assert CNF(Clause()).isTrivialUnsat

    # inversion
    assert ~CNF({Clause([2,3]), Clause([4,5])}) == CNF({Clause([-2,-4]), Clause([-2,-5]), Clause([-3,-4]), Clause([-3,-5])})
    assert len(~CNF({Clause([2, 3, 4]), Clause([5, 6, 7]), Clause([8,9,10])})) == 27
    assert not CNF({Clause([2]), Clause([-2,3]), Clause([3,4])}).isTrivialUnsat
    
    # removeImplied
    assert CNF({Clause([2,3]), Clause([2,3,4]), Clause([3,4])} ,keep_minimal=True) == CNF({Clause([2,3]), Clause([3,4])})