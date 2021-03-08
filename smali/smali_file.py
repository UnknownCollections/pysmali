import warnings
from typing import Iterator, List, Optional, Union, Type

from smali.attributes import StatementAttributes
from smali.block import Block, BlockItemType
from smali.exceptions import FormatError, ParseError, ValidationError, ValidationWarning, WhitespaceWarning
from smali.lib.smali_compare import SmaliCompare
from smali.statements import Statement, MethodStatement, FieldStatement, StatementType


class SmaliFile:
    __version__ = None
    VALIDATE: bool = False

    raw_code: str
    lines: Iterator[str]
    root: Block

    def __init__(self, smali_code: str):
        self.raw_code = smali_code
        self.lines = smali_code.splitlines()
        self.root = Block()
        self.parse()
        if SmaliFile.VALIDATE:
            self.validate()

    @classmethod
    def parse_file(cls, file_path: str) -> 'SmaliFile':
        with open(file_path, 'r') as f:
            smali_code = f.read()
        return cls(smali_code)

    def __str__(self):
        result = []
        statements = self.root.flatten()
        block_level = 0
        for idx, statement in enumerate(statements):
            if bool(statement.attributes & StatementAttributes.BLOCK_END):
                block_level -= 1
                if block_level < 0:
                    raise FormatError('block level became negative in BLOCK_END')

            if bool(statement.attributes & StatementAttributes.NO_INDENT):
                indent = ''
            else:
                indent = (block_level * Block.INDENT_SIZE) * Block.INDENT_CHAR

            if bool(statement.attributes & StatementAttributes.ASSIGNMENT_LHS):
                result.append(f'{indent}{statement}= ')
            elif bool(statement.attributes & StatementAttributes.ASSIGNMENT_RHS):
                result[-1] += str(statement)
            elif bool(statement.attributes & StatementAttributes.NO_BREAK):
                if bool(statement.attributes & StatementAttributes.BLOCK_END) and bool(statements[idx - 1].attributes & StatementAttributes.BLOCK_START):
                    result[-1] += str(statement)
                else:
                    result[-1] += f' {statement}'
            else:
                result.append(f'{indent}{statement}')

            if bool(statement.attributes & StatementAttributes.BLOCK_START):
                block_level += 1

        return '\n'.join(result)

    def parse_statements(self, statements: List[Statement]):
        stack: List[Block] = []
        for statement in statements:
            if bool(statement.attributes & StatementAttributes.BLOCK_START):
                # If a new block is starting, generate a new block on the stack
                #  and add the block start statement
                stack.append(Block())
                stack[-1].append(statement)
            elif bool(statement.attributes & StatementAttributes.BLOCK_END):
                # A block is ending, finish it
                finished_block = stack.pop()
                if finished_block.head.block_ends_with != (type(statement), statement.modifiers):
                    raise ParseError('block end does not match block start')
                finished_block.append(statement)
                # If there are more blocks on the stack, this block appends to that
                if len(stack) > 0:
                    stack[-1].append(finished_block)
                else:
                    # No more blocks in the stack, we're back to root
                    self.root.append(finished_block)
            else:
                # If it's not a start or end, it's a normal statement
                # First check to see if we're in a maybe block
                # Check to see if there is a block on the stack and append it there
                # Otherwise it's root
                if len(stack) > 0:
                    stack[-1].append(statement)
                else:
                    self.root.append(statement)
        if len(stack) > 0:
            raise ParseError('file parsing complete but block stack is not empty')

    def parse(self):
        statements: List[Statement] = []
        maybe_block_indexes: List[int] = []
        # Some statements can either be a single line or multiple line blocks
        # The way we handle this is to do 2 parse passes, the first pass determines if the variable statements
        #  are a single line or multiple lines. The second pass parses into blocks.
        for line in self.lines:
            new_statements = Statement.parse_line(line)
            # A line can contain multiple statements: `{}` or `statement1 = statement2`
            for new_statement in new_statements:
                statements.append(new_statement)
                if bool(new_statement.attributes & StatementAttributes.MAYBE_BLOCK_START):
                    # If the statement might start a block, keep track of it
                    maybe_block_indexes.append(len(statements) - 1)
                elif bool(new_statement.attributes & StatementAttributes.BLOCK_END):
                    # If we reach and end statement, check to see if it matches any possible MAYBE_BLOCK_START
                    for maybe_block_index in reversed(maybe_block_indexes):
                        if statements[maybe_block_index].block_ends_with == (type(new_statement), new_statement.modifiers):
                            # If the MAYBE_BLOCK_START statement is a block start, set it's attribute to BLOCK_START
                            statements[maybe_block_index].attributes |= StatementAttributes.BLOCK_START
                            statements[maybe_block_index].attributes &= ~StatementAttributes.MAYBE_BLOCK_START
                            maybe_block_indexes.remove(maybe_block_index)
                            break

        # For all MAYBE_BLOCK_START statements that remain, set their attribute to SINGLE_LINE
        for maybe_block_index in maybe_block_indexes:
            statements[maybe_block_index].attributes |= StatementAttributes.SINGLE_LINE
            statements[maybe_block_index].attributes &= ~StatementAttributes.MAYBE_BLOCK_START

        self.parse_statements(statements)

    def validate(self):
        reconstruction = str(self)
        if SmaliCompare.order_independent_hash(self.raw_code) != SmaliCompare.order_independent_hash(reconstruction):
            raise ValidationError(f'not reconstructed correctly')
        elif not SmaliCompare.whitespace_normalized_equals(self.raw_code, reconstruction):
            warnings.warn(ValidationWarning(f'might not be reconstructed correctly'))
        elif self.raw_code.rstrip() != reconstruction.rstrip():
            warnings.warn(WhitespaceWarning(f'has different whitespace'))

    def find(self, stmt_type: Type[StatementType], **attributes) -> List[BlockItemType]:
        return self.root.find(stmt_type, **attributes)

    def find_methods(self, method_name: str) -> List[MethodStatement]:
        return self.root.find(MethodStatement, method_name=method_name)

    def find_method(self, method_name: str, method_prototype: str) -> Optional[Block]:
        method_parts = MethodStatement.RE_METHOD_PROTOTYPE.fullmatch(method_prototype)
        if method_parts is None:
            raise Exception('invalid method prototype')
        result = self.root.find(MethodStatement, method_name=method_name, method_params=method_parts.group(1), method_result_type=method_parts.group(2))
        if len(result) == 0:
            return None
        return result[0]

    def find_field(self, field_name: str) -> Optional[Union[Block, FieldStatement]]:
        result = self.root.find(FieldStatement, member_name=field_name)
        if len(result) == 0:
            return None
        return result[0]
