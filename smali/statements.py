import re
import warnings
from abc import ABCMeta, abstractmethod
from typing import Dict, Iterable, List, Optional, Tuple, Type, Union

from more_itertools import peekable

from smali.attributes import StatementAttributes
from smali.exceptions import ParseError, ValidationError, ValidationWarning, WhitespaceWarning
from smali.literals import IntLiteral
from smali.modifiers import EndModifiers, Modifiers
from smali.qualifiers import Qualifier
from smali.tokens import Annotation, ArrayData, Catch, CatchAll, Class, End, Enum, Field, Implements, Line, Local, Locals, Method, PackedSwitch, Param, Prologue, Registers, Restart, Source, SparseSwitch, Subannotation, Super, Token, Tokens, TokensLex
from smali.utils import ValidationComparison


class Statement(metaclass=ABCMeta):
    VALIDATE: bool = False

    RE_SPACE_SPLIT = re.compile(r' +(?=(?:[^"\\]*(?:\\.|"(?:[^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
    RE_ASSIGNMENT_SPLIT = re.compile(r'=(?=(?:[^"\\]*(?:\\.|"(?:[^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
    RE_EOL_COMMENT = re.compile(r'\s*(?:#.*)?$')
    RE_BRACKET_BLOCK_SPLIT = re.compile(r'(?:(?:({) ?)|(?: ?(})))')

    raw_line: str
    clean_line: str
    eol_comment: str
    line_iter: Union[peekable, Iterable[str]]
    modifiers: Optional[Modifiers]
    attributes: StatementAttributes

    def __init__(self, line: str):
        self.raw_line = line.rstrip('\r\n')
        self.clean_line = self.raw_line.lstrip()
        self.parse_eol_comment()
        self.line_iter = peekable(Statement.RE_SPACE_SPLIT.split(self.clean_line))
        self.modifiers = None
        self.parse_token()
        self.parse_modifiers()
        self.parse()
        if Statement.VALIDATE:
            self.assert_end_of_line()
            self.validate()

    @classmethod
    def parse_line(cls, line: str) -> List['Statement']:
        clean_line = line.strip()
        if len(clean_line) == 0:
            return [BlankStatement(line)]
        elif clean_line[0] == Qualifier.COMMENT:
            return [CommentStatement(line)]
        elif Statement.RE_ASSIGNMENT_SPLIT.search(clean_line) is not None:
            assignment_line = Statement.RE_ASSIGNMENT_SPLIT.split(clean_line, maxsplit=1)
            if len(assignment_line) != 2:
                raise ParseError('assignment statement does not have correct number of sides')
            lhs = Statement.parse_line(assignment_line[0])
            lhs[0].attributes |= StatementAttributes.ASSIGNMENT_LHS
            rhs = Statement.parse_line(assignment_line[1])
            rhs[0].attributes |= StatementAttributes.ASSIGNMENT_RHS
            return [*lhs, *rhs]
        elif clean_line[-1] == Qualifier.BLOCK_END:
            if len(clean_line) > 1:
                statements = []
                block_statement_parts = list(filter(lambda x: x and x.strip() != '', Statement.RE_BRACKET_BLOCK_SPLIT.split(clean_line)))
                for part in block_statement_parts:
                    statements.extend(Statement.parse_line(part))

                for statement in statements[1:]:
                    statement.attributes |= StatementAttributes.NO_BREAK

                return statements

            return [BlockEndStatement(line)]
        elif clean_line[-1] == Qualifier.BLOCK_START:
            return [BlockStartStatement(line)]
        elif clean_line[0] == Qualifier.BLOCK_START:
            statements = []
            block_statement_parts = list(filter(lambda x: x and x.strip() != '', Statement.RE_BRACKET_BLOCK_SPLIT.split(clean_line)))
            for part in block_statement_parts:
                statements.extend(Statement.parse_line(part))

            for statement in statements[1:]:
                statement.attributes |= StatementAttributes.NO_BREAK

            return statements
        elif clean_line[0] == Qualifier.TOKEN:
            line_parts = clean_line.split(' ')
            if len(line_parts[0]) <= 1:
                raise ParseError('token descriptor too small')
            token_str = line_parts[0][1:]
            if token_str not in Tokens:
                raise ParseError('unknown or invalid token descriptor')
            if Tokens[token_str] not in StatementTypes:
                raise ParseError('unsupported token')
            return [StatementTypes[Tokens[token_str]](line)]
        else:
            return [BodyStatement(line)]

    @classmethod
    def parse_lines(cls, lines: List[str]) -> List['Statement']:
        result = []
        for line in lines:
            result.extend(cls.parse_line(line))
        return result

    def parse_eol_comment(self):
        self.eol_comment = ''
        eol_comment_match = Statement.RE_EOL_COMMENT.search(self.clean_line)
        if eol_comment_match is not None:
            self.eol_comment = eol_comment_match.group(0)
            match_idx = eol_comment_match.span()
            self.clean_line = self.clean_line[:match_idx[0]] + self.clean_line[match_idx[1]:]

    def parse_token(self):
        if self.token is None:
            return
        if self.descriptor != next(self.line_iter):
            raise ParseError('statement does not start with correct token')

    def parse_modifiers(self):
        if self.token is None:
            return
        if self.token.AVAILABLE_MODIFIERS is None:
            return
        try:
            self.modifiers = self.token.AVAILABLE_MODIFIERS(0)  # noqa
            while True:
                mod = self.token.AVAILABLE_MODIFIERS.find(self.line_iter.peek())
                if mod is None:
                    break
                self.modifiers |= mod
                next(self.line_iter)
            if self.modifiers == self.token.AVAILABLE_MODIFIERS(0):  # noqa
                self.modifiers = None
        except StopIteration:
            pass

    def assert_end_of_line(self):
        if self.line_iter:
            raise ParseError(f'{type(self).__name__} line not empty after parsing: {self.raw_line}')

    def finish_line(self):
        while self.line_iter:
            next(self.line_iter)

    def validate(self):
        reconstructed = str(self)
        if ValidationComparison.order_independent_hash(self.raw_line) != ValidationComparison.order_independent_hash(reconstructed):
            raise ValidationError(f'source line DOES NOT match reconstruction\n\t[SOURCE] {self.raw_line.lstrip()}\n\t[PARSED] {str(self)}')
        elif not ValidationComparison.whitespace_normalized_equals(self.raw_line, reconstructed):
            warnings.warn(ValidationWarning(f'source line might not match reconstruction\n\t[SOURCE] {self.raw_line.lstrip()}\n\t[PARSED] {str(self)}'))
        elif self.raw_line.lstrip() != reconstructed:
            warnings.warn(WhitespaceWarning(f'source line might have different whitespace\n\t[SOURCE] {self.raw_line.lstrip()}\n\t[PARSED] {str(self)}'))

    @property
    def token(self) -> Optional[Type[Token]]:
        return None

    @property
    def descriptor(self) -> Optional[str]:
        if self.token is None:
            return ''
        return f'{Qualifier.TOKEN}{TokensLex[self.token]}'

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return None

    @abstractmethod
    def parse(self):
        raise NotImplementedError()

    @abstractmethod
    def __str__(self):
        raise NotImplementedError


class BlankStatement(Statement):

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE | StatementAttributes.NO_INDENT
        self.finish_line()

    def __str__(self):
        return ''


class CommentStatement(Statement):

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.finish_line()

    def __str__(self):
        return self.raw_line.lstrip()


class BlockStartStatement(Statement):

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_START
        self.finish_line()

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return BlockEndStatement, None

    def __str__(self):
        return f'{self.raw_line.lstrip()}{self.eol_comment}'


class BlockEndStatement(Statement):

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_END
        self.finish_line()

    def __str__(self):
        return f'}}{self.eol_comment}'


class BodyStatement(Statement):

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.finish_line()

    def __str__(self):
        return f'{self.clean_line}{self.eol_comment}'


class AnnotationStatement(Statement):
    class_descriptor: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Annotation

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.ANNOTATION

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_START
        self.class_descriptor = next(self.line_iter)

    def __str__(self):
        return f'{self.descriptor} {self.modifiers} {self.class_descriptor}{self.eol_comment}'


class ArrayDataStatement(Statement):
    element_width: IntLiteral

    @property
    def token(self) -> Optional[Type[Token]]:
        return ArrayData

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.ARRAY_DATA

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_START
        self.element_width = IntLiteral(next(self.line_iter))

    def __str__(self):
        return f'{self.descriptor} {self.element_width}{self.eol_comment}'


class CatchStatement(Statement):
    type_descriptor: str
    try_start_label: str
    try_end_label: str
    catch_label: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Catch

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.type_descriptor = next(self.line_iter)
        self.try_start_label = next(self.line_iter)[2:]
        next(self.line_iter)
        self.try_end_label = next(self.line_iter)[1:-1]
        self.catch_label = next(self.line_iter)[1:]

    def __str__(self):
        return f'{self.descriptor} {self.type_descriptor} {{:{self.try_start_label} .. :{self.try_end_label}}} :{self.catch_label}{self.eol_comment}'


class CatchAllStatement(Statement):
    try_start_label: str
    try_end_label: str
    catch_label: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return CatchAll

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.try_start_label = next(self.line_iter)[2:]
        next(self.line_iter)
        self.try_end_label = next(self.line_iter)[1:-1]
        self.catch_label = next(self.line_iter)[1:]

    def __str__(self):
        return f'{self.descriptor} {{:{self.try_start_label} .. :{self.try_end_label}}} :{self.catch_label}{self.eol_comment}'


class ClassStatement(Statement):
    class_descriptor: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Class

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.class_descriptor = next(self.line_iter)

    def __str__(self):
        if self.modifiers is not None:
            return f'{self.descriptor} {self.modifiers} {self.class_descriptor}{self.eol_comment}'
        else:
            return f'{self.descriptor} {self.class_descriptor}{self.eol_comment}'


class EndStatement(Statement):
    local_register: Optional[str]

    @property
    def token(self) -> Optional[Type[Token]]:
        return End

    def parse(self):
        if self.modifiers == EndModifiers.LOCAL:
            self.attributes = StatementAttributes.SINGLE_LINE
            self.local_register = next(self.line_iter)
        else:
            self.attributes = StatementAttributes.BLOCK_END

    def __str__(self):
        if self.modifiers == EndModifiers.LOCAL:
            return f'{self.descriptor} {self.modifiers} {self.local_register}{self.eol_comment}'
        else:
            return f'{self.descriptor} {self.modifiers}{self.eol_comment}'


class EnumStatement(Statement):
    enum_directive: str
    field_reference: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Enum

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.field_reference = next(self.line_iter)

    def __str__(self):
        return f'{self.descriptor} {self.field_reference}{self.eol_comment}'


class FieldStatement(Statement):
    member_name: str
    type_descriptor: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Field

    def parse(self):
        self.attributes = StatementAttributes.MAYBE_BLOCK_START
        field_parts = next(self.line_iter).split(':')
        self.member_name = field_parts[0]
        self.type_descriptor = field_parts[1]

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.FIELD

    def __str__(self):
        if self.modifiers is not None:
            return f'{self.descriptor} {self.modifiers} {self.member_name}:{self.type_descriptor}{self.eol_comment}'
        else:
            return f'{self.descriptor} {self.member_name}:{self.type_descriptor}{self.eol_comment}'


class ImplementsStatement(Statement):
    class_descriptor: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Implements

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.class_descriptor = next(self.line_iter)

    def __str__(self):
        return f'{self.descriptor} {self.class_descriptor}{self.eol_comment}'


class LineStatement(Statement):
    line_no: IntLiteral

    @property
    def token(self) -> Optional[Type[Token]]:
        return Line

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.line_no = IntLiteral(next(self.line_iter))

    def __str__(self):
        return f'{self.descriptor} {self.line_no}{self.eol_comment}'


class LocalStatement(Statement):
    register: str
    variable_name: Optional[str]
    variable_type_descriptor: Optional[str]
    literal: Optional[str]

    @property
    def token(self) -> Optional[Type[Token]]:
        return Local

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.register = next(self.line_iter)
        self.variable_name = None
        self.variable_type_descriptor = None
        self.literal = None
        if self.register.endswith(','):
            self.register = self.register[:-1]
            variable_parts = next(self.line_iter).split(':')
            self.variable_name = variable_parts[0]
            self.variable_type_descriptor = variable_parts[1]
            if self.variable_type_descriptor.endswith(','):
                self.variable_type_descriptor = self.variable_type_descriptor[:-1]
                self.literal = next(self.line_iter)

    def __str__(self):
        result = f'{self.descriptor} {self.register}'
        if self.variable_name is not None and self.variable_type_descriptor is not None:
            result = f'{result}, {self.variable_name}:{self.variable_type_descriptor}'
            if self.literal is not None:
                result = f'{result}, {self.literal}'
        return f'{result}{self.eol_comment}'


class LocalsStatement(Statement):
    local_count: IntLiteral

    @property
    def token(self) -> Optional[Type[Token]]:
        return Locals

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.local_count = IntLiteral(next(self.line_iter))

    def __str__(self):
        return f'{self.descriptor} {self.local_count}{self.eol_comment}'


class MethodStatement(Statement):
    RE_METHOD = re.compile(r'^(.*?)\((.*)\)(.*)$')
    member_name: str
    method_params: str
    method_result_type: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Method

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_START
        method = MethodStatement.RE_METHOD.fullmatch(next(self.line_iter))
        if method is None:
            raise ParseError(f'MethodStatement unable to parse method prototype: {self.raw_line}')
        self.member_name, self.method_params, self.method_result_type = method.group(1, 2, 3)

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.METHOD

    def __str__(self):
        if self.modifiers is not None:
            return f'{self.descriptor} {self.modifiers} {self.member_name}({self.method_params}){self.method_result_type}{self.eol_comment}'
        else:
            return f'{self.descriptor} {self.member_name}({self.method_params}){self.method_result_type}{self.eol_comment}'


class PackedSwitchStatement(Statement):
    switch_literal: IntLiteral

    @property
    def token(self) -> Optional[Type[Token]]:
        return PackedSwitch

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_START
        self.switch_literal = IntLiteral(next(self.line_iter))

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.PACKED_SWITCH

    def __str__(self):
        return f'{self.descriptor} {self.switch_literal}{self.eol_comment}'


class ParamStatement(Statement):
    register: str
    register_literal: Optional[str]

    @property
    def token(self) -> Optional[Type[Token]]:
        return Param

    def parse(self):
        self.attributes = StatementAttributes.MAYBE_BLOCK_START
        self.register = next(self.line_iter)
        if self.register.endswith(','):
            self.register = self.register[:-1]
            self.register_literal = next(self.line_iter)
        else:
            self.register_literal = None

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.PARAM

    def __str__(self):
        if self.register_literal is None:
            return f'{self.descriptor} {self.register}{self.eol_comment}'
        else:
            return f'{self.descriptor} {self.register}, {self.register_literal}{self.eol_comment}'


class PrologueStatement(Statement):

    @property
    def token(self) -> Optional[Type[Token]]:
        return Prologue

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE

    def __str__(self):
        return f'{self.descriptor}{self.eol_comment}'


class RegistersStatement(Statement):
    register_count: IntLiteral

    @property
    def token(self) -> Optional[Type[Token]]:
        return Registers

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.register_count = IntLiteral(next(self.line_iter))

    def __str__(self):
        return f'{self.descriptor} {self.register_count}{self.eol_comment}'


class RestartStatement(Statement):
    register: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Restart

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.register = next(self.line_iter)

    def __str__(self):
        return f'{self.descriptor} {self.modifiers} {self.register}{self.eol_comment}'


class SourceStatement(Statement):
    source_target: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Source

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.source_target = next(self.line_iter)[1:-1]

    def __str__(self):
        return f'{self.descriptor} "{self.source_target}"{self.eol_comment}'


class SparseSwitchStatement(Statement):

    @property
    def token(self) -> Optional[Type[Token]]:
        return SparseSwitch

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_START

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.SPARSE_SWITCH

    def __str__(self):
        return f'{self.descriptor}{self.eol_comment}'


class SubannotationStatement(Statement):
    class_descriptor: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Subannotation

    def parse(self):
        self.attributes = StatementAttributes.BLOCK_START
        self.class_descriptor = next(self.line_iter)

    @property
    def block_ends_with(self) -> Optional[Tuple[Type['Statement'], Optional[Modifiers]]]:
        return EndStatement, EndModifiers.SUBANNOTATION

    def __str__(self):
        return f'{self.descriptor} {self.class_descriptor}{self.eol_comment}'


class SuperStatement(Statement):
    class_descriptor: str

    @property
    def token(self) -> Optional[Type[Token]]:
        return Super

    def parse(self):
        self.attributes = StatementAttributes.SINGLE_LINE
        self.class_descriptor = next(self.line_iter)

    def __str__(self):
        return f'{self.descriptor} {self.class_descriptor}{self.eol_comment}'


StatementTypes: Dict[Type[Token], Type[Statement]] = {
    Annotation: AnnotationStatement,
    ArrayData: ArrayDataStatement,
    Catch: CatchStatement,
    CatchAll: CatchAllStatement,
    Class: ClassStatement,
    End: EndStatement,
    Enum: EnumStatement,
    Field: FieldStatement,
    Implements: ImplementsStatement,
    Line: LineStatement,
    Local: LocalStatement,
    Locals: LocalsStatement,
    Method: MethodStatement,
    PackedSwitch: PackedSwitchStatement,
    Param: ParamStatement,
    Prologue: PrologueStatement,
    Registers: RegistersStatement,
    Restart: RestartStatement,
    Source: SourceStatement,
    SparseSwitch: SparseSwitchStatement,
    Subannotation: SubannotationStatement,
    Super: SuperStatement
}
