class IntLiteral(int):
    base: int

    def __new__(cls, literal: str):
        base = IntLiteral.parse_base(literal)
        i = super(IntLiteral, cls).__new__(cls, literal, base)
        i.base = base
        return i

    def __str__(self):
        if self.base == 16:
            return hex(self)
        else:
            return super(IntLiteral, self).__str__()

    @staticmethod
    def parse_base(literal: str) -> int:
        literal = literal.lower().lstrip('-')
        if literal.startswith('0x'):
            return 16
        else:
            return 10
