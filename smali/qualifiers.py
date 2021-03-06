from enum import Enum


class Qualifier(Enum):
    BLOCK_START = '{'
    BLOCK_END = '}'
    COMMENT = '#'
    TOKEN = '.'
    LABEL = ':'

    def __eq__(self, other):
        if type(other) == str:
            return self.value == other
        return self == other

    def __str__(self):
        return self.value
