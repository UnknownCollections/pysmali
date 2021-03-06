from typing import List, Union

from smali.exceptions import FormatError
from smali.statements import Statement


class Block:
    INDENT_SIZE = 4
    INDENT_CHAR = ' '

    items: List[Union[Statement, 'Block']]

    def __init__(self):
        self.items = []

    def append(self, item: Union[Statement, 'Block']):
        self.items.append(item)

    def extend(self, items: List[Union[Statement, 'Block']]):
        self.items.extend(items)

    @property
    def type(self) -> Statement:
        if isinstance(self.items[0], Statement):
            return self.items[0]
        else:
            return self.items[0].type

    def flatten(self) -> List[Statement]:
        result = []
        for item in self.items:
            if isinstance(item, Statement):
                result.append(item)
            elif isinstance(item, Block):
                result.extend(item.flatten())
            else:
                raise FormatError(f'invalid item type: {type(item)}')
        return result
