from turtledemo.sorting_animate import Block
from typing import List, Union, Type, NewType

from smali.exceptions import FormatError
from smali.statements import Statement, StatementType

BlockItem = NewType('BlockItem', Union[Statement, 'Block'])
BlockItemType = NewType('BlockItemType', Union[StatementType, 'Block'])


class Block:
    INDENT_SIZE = 4
    INDENT_CHAR = ' '

    items: List[BlockItem]

    def __init__(self):
        self.items = []

    def append(self, item: BlockItem):
        self.items.append(item)

    def extend(self, items: List[BlockItem]):
        self.items.extend(items)

    @property
    def head(self) -> Statement:
        if isinstance(self.items[0], Statement):
            return self.items[0]
        else:
            return self.items[0].head

    @property
    def type(self) -> Type[Statement]:
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

    @staticmethod
    def _match_item(item: Statement, **attributes) -> bool:
        for key, value in attributes.items():
            if hasattr(item, key) and getattr(item, key) != value:
                return False
        return True

    def find(self, stmt_type: Type[StatementType], **kwargs) -> List[BlockItemType]:
        result = []
        for item in self.items:
            if isinstance(item, Block):
                if isinstance(item.head, stmt_type) and Block._match_item(item.head, **kwargs):
                    result.append(item)
                result.extend(item.find(stmt_type, **kwargs))
            elif isinstance(item, stmt_type) and Block._match_item(item, **kwargs):
                result.append(item)
        return result
