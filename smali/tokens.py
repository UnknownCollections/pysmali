from abc import ABCMeta
from typing import Dict, Optional, Type

from smali.modifiers import AnnotationModifiers, ClassModifiers, EndModifiers, FieldModifiers, MethodModifiers, Modifiers, RestartModifiers


class Token(metaclass=ABCMeta):
    AVAILABLE_MODIFIERS: Optional[Type[Modifiers]] = None


class Annotation(Token):
    AVAILABLE_MODIFIERS = AnnotationModifiers


class ArrayData(Token):
    AVAILABLE_MODIFIERS = None


class Catch(Token):
    AVAILABLE_MODIFIERS = None


class CatchAll(Token):
    AVAILABLE_MODIFIERS = None


class Class(Token):
    AVAILABLE_MODIFIERS = ClassModifiers


class End(Token):
    AVAILABLE_MODIFIERS = EndModifiers


class Enum(Token):
    AVAILABLE_MODIFIERS = None


class Field(Token):
    AVAILABLE_MODIFIERS = FieldModifiers


class Implements(Token):
    AVAILABLE_MODIFIERS = None


class Line(Token):
    AVAILABLE_MODIFIERS = None


class Local(Token):
    AVAILABLE_MODIFIERS = None


class Locals(Token):
    AVAILABLE_MODIFIERS = None


class Method(Token):
    AVAILABLE_MODIFIERS = MethodModifiers


class PackedSwitch(Token):
    AVAILABLE_MODIFIERS = None


class Param(Token):
    AVAILABLE_MODIFIERS = None


class Prologue(Token):
    AVAILABLE_MODIFIERS = None


class Registers(Token):
    AVAILABLE_MODIFIERS = None


class Restart(Token):
    AVAILABLE_MODIFIERS = RestartModifiers


class Source(Token):
    AVAILABLE_MODIFIERS = None


class SparseSwitch(Token):
    AVAILABLE_MODIFIERS = None


class Subannotation(Token):
    AVAILABLE_MODIFIERS = None


class Super(Token):
    AVAILABLE_MODIFIERS = None


Tokens: Dict[str, Type[Token]] = {
    'annotation': Annotation,
    'array-data': ArrayData,
    'catch': Catch,
    'catchall': CatchAll,
    'class': Class,
    'end': End,
    'enum': Enum,
    'field': Field,
    'implements': Implements,
    'line': Line,
    'local': Local,
    'locals': Locals,
    'method': Method,
    'packed-switch': PackedSwitch,
    'param': Param,
    'prologue': Prologue,
    'registers': Registers,
    'restart': Restart,
    'source': Source,
    'sparse-switch': SparseSwitch,
    'subannotation': Subannotation,
    'super': Super,
}
TokensLex = {v: k for k, v in Tokens.items()}
