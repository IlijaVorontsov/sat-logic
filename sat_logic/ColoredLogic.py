from sat_logic.Logic import CNF

class ColoredCNF(CNF):
    console_colors = {0: '\033[92m', 1: '\033[94m', 2: '\033[96m'}

    def __init__(self,clauses=[], color=0, keep_minimal=False):
        super().__init__(clauses, keep_minimal=keep_minimal)
        self.color = color

    def __repr__(self):
        return super().__str__() + f" [{self.color}]"
    
    def __str__(self):
        return ColoredCNF.console_colors[self.color] + super().__str__() + '\033[0m'
    
    @staticmethod
    def fromCNF(cnf: CNF, color=0):
        return ColoredCNF(cnf.clauses, color, keep_minimal=cnf.keep_minimal)
    
class ColorfulCNF(CNF):
    def __init__(self,cnfs=list[CNF], keep_minimal=False):
        self.color = list()
        clauses = set()
        for i in range(len(cnfs)):
            clauses.update(cnfs[i].clauses)
            self.color.append(ColoredCNF.fromCNF(cnfs[i], i))
        super().__init__(clauses, keep_minimal=keep_minimal)
 
if __name__ == "__main__":
    cnf1 = CNF([[2,3], [3,4]])
    cnf2 = CNF([[2,3], [3,4]])
    c = ColorfulCNF([cnf1, cnf2])
    print(c.color[0])
