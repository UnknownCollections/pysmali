from typing import List, Union, Type, NewType, Generic

from smali.exceptions import FormatError
from smali.statements import Statement, StatementType

BlockItem = NewType('BlockItem', Union[Statement, 'Block'])
BlockItemType = NewType('BlockItemType', Union[StatementType, 'Block[StatementType]'])


class Block(Generic[StatementType]):
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
    def head(self) -> StatementType:
        if isinstance(self.items[0], Statement):
            return self.items[0]
        else:
            return self.items[0].head

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
            if not hasattr(item, key):
                return False
            if getattr(item, key) != value:
                return False
        return True

    def find(self, stmt_type: Type[StatementType], **kwargs) -> List[BlockItemType]:
        result = []
        for item in self.items:
            if isinstance(item, Block):
                if isinstance(item.head, stmt_type) and Block._match_item(item.head, **kwargs):
                    result.append(item)
                else:
                    result.extend(item.find(stmt_type, **kwargs))
            elif isinstance(item, stmt_type) and Block._match_item(item, **kwargs):
                result.append(item)
        return result
