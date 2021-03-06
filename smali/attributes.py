from enum import Flag, auto


class StatementAttributes(Flag):
    SINGLE_LINE = auto()
    BLOCK_START = auto()
    MAYBE_BLOCK_START = auto()
    BLOCK_END = auto()
    ASSIGNMENT_LHS = auto()
    ASSIGNMENT_RHS = auto()
    NO_BREAK = auto()
    NO_INDENT = auto()
