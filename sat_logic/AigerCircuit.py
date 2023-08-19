from sat_logic.Logic import CNF, Clause, Literal

class AigerCircuit:
    def __init__(self, filename: str):
        with open(filename, "r") as aigerfile:
            header = aigerfile.readline().split()
            self.maxvar = int(header[1]) + 2 # x_1 reserved for true and x_maxvar for assumption variable
            self.switching_variable = self.maxvar

            self.b = CNF()

            # skip over inputs
            for _ in range(int(header[2])):
                aigerfile.readline()

            self.latches = []
            for _ in range(int(header[3])):
                latch = AigerCircuit.parse_line(aigerfile)
                assert len(latch) == 2
                self.latches.append(latch)

            assert int(header[4]) == 1 # Bad state detector by assignment (only one output state)
            output = AigerCircuit.parse_line(aigerfile)
            assert len(output) == 1
            self.output = output[0]

            self.and_gates = []
            for _ in range(int(header[5])):
                and_gate = AigerCircuit.parse_line(aigerfile)
                assert len(and_gate) == 3
                self.and_gates.append(and_gate)
                
    def clauses_gates(self, tick: int):
        assert tick >= 0
        clauses = set()
        for and_gate in self.and_gates:
            output = self.literalAt(Literal(and_gate[0]), tick)
            input1 = self.literalAt(Literal(and_gate[1]), tick)
            input2 = self.literalAt(Literal(and_gate[2]), tick)
            clauses.update({
                Clause([~output, input1]),
                Clause([~output, input2]), 
                Clause([output, ~input1, ~input2])
            })
        return CNF(clauses)

    def clauses_latches(self, tick: int):
        assert tick >= 0
        if tick == 0:
            return CNF({Clause([-latch[0]]) for latch in self.latches})
        clauses = set()
        for latch in self.latches:
            output = self.literalAt(Literal(latch[0]), tick)
            input  = self.literalAt(Literal(latch[1]), tick-1)
            clauses.update({
                Clause([~output, input]), 
                Clause([output, ~input])
            })
        return CNF(clauses)
    
    def clauses_system(self, tick: int):
        assert tick >= 0
        clauses = self.clauses_gates(tick) & self.clauses_latches(tick)
        if tick > 1:
            self.b = self.b & clauses
        return clauses

    def clause_output(self, tick: int):
        return Clause(self.literalAt(Literal(self.output), tick))
    
    def literalAt(self, literal: Literal, tick: int) -> int:
        if literal.isTrue or literal.isFalse:
            return literal
        
        variable_at_0 = (literal.variable - 1)%self.maxvar + 1 # shifting because maxvar = switching_variable;
        variable_at_tick = variable_at_0 + tick*self.maxvar
        return Literal(literal.polarity*variable_at_tick)

    def cnfAtTick(self, cnf: CNF, tick: int) -> CNF:
        result = set()
        for clause in cnf:
            new = set()
            for literal in clause:
                new.add(self.literalAt(literal, tick))
            result.add(Clause(new))
        return CNF(result)
    
    def applySwitch(self, cnf: CNF, tick: int) -> CNF:
        return cnf | CNF({Clause([self.switching_variable*(tick+1)])})
    
    def assumptions(self,tick: int):
        # All switches are on expect the last one
        return [self.switching_variable*(i+1) for i in range(tick)] + [-self.switching_variable*(tick+1)]

    @staticmethod
    def parse_line(file):
        return [AigerCircuit.parse_variable(number) for number in file.readline().split()]

    # Remaps the AIGER variables to DIMACS variables.
    # Since the AIGER x_0 is always true, we map it to DIMACS variable 1.
    # All other variables are shifted by 1.
    @staticmethod
    def parse_variable(number_string: str) -> int:
        number = int(number_string)
        if number == 0:
            return -1
        elif number == 1:
            return 1
        elif number%2 == 0:
            return number//2 + 1
        else:
            return -(number//2) - 1