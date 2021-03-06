from enum import Flag, auto
from typing import Optional, Type


class Modifiers(Flag):
    def __str__(self):
        if self.name and self.name != '':
            return self.name.lower().replace('_', '-')

        result = []
        for c in self.__class__:
            if c.value & self.value == c.value:
                result.append(c.name.lower().replace('_', '-'))

        if len(result) > 0:
            return ' '.join(result)

        return ''

    @classmethod
    def find(cls: Type['Modifiers'], modifier_tag: str) -> Optional['Modifiers']:
        for c in cls:
            modifier_name = str(c)
            if modifier_name is not None and modifier_name == modifier_tag:
                return c
        return None


class AnnotationModifiers(Modifiers):
    BUILD = auto()
    RUNTIME = auto()
    SYSTEM = auto()


class ClassModifiers(Modifiers):
    _order_ = 'PUBLIC PRIVATE PROTECTED STATIC FINAL INTERFACE ABSTRACT SYNTHETIC ANNOTATION ENUM'
    PUBLIC = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    STATIC = auto()
    FINAL = auto()
    INTERFACE = auto()
    ABSTRACT = auto()
    SYNTHETIC = auto()
    ANNOTATION = auto()
    ENUM = auto()


class EndModifiers(Modifiers):
    ANNOTATION = auto()
    ARRAY_DATA = auto()
    FIELD = auto()
    LOCAL = auto()
    METHOD = auto()
    PACKED_SWITCH = auto()
    PARAM = auto()
    SPARSE_SWITCH = auto()
    SUBANNOTATION = auto()


class FieldModifiers(Modifiers):
    _order_ = 'PUBLIC PRIVATE PROTECTED STATIC FINAL VOLATILE BRIDGE TRANSIENT SYNTHETIC ENUM'
    PUBLIC = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    STATIC = auto()
    FINAL = auto()
    VOLATILE = auto()
    BRIDGE = auto()
    TRANSIENT = auto()
    SYNTHETIC = auto()
    ENUM = auto()


class MethodModifiers(Modifiers):
    _order_ = 'PUBLIC PRIVATE PROTECTED STATIC FINAL SYNCHRONIZED BRIDGE VARARGS NATIVE INTERFACE ABSTRACT STRICTFP SYNTHETIC CONSTRUCTOR DECLARED_SYNCHRONIZED'
    PUBLIC = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    STATIC = auto()
    FINAL = auto()
    SYNCHRONIZED = auto()
    BRIDGE = auto()
    VARARGS = auto()
    NATIVE = auto()
    INTERFACE = auto()
    ABSTRACT = auto()
    STRICTFP = auto()
    SYNTHETIC = auto()
    CONSTRUCTOR = auto()
    DECLARED_SYNCHRONIZED = auto()


class RestartModifiers(Modifiers):
    LOCAL = auto()
