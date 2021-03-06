class ParseError(Exception):
    ...


class FormatError(Exception):
    ...


class ValidationError(Exception):
    ...


class ValidationWarning(Warning):
    ...


class WhitespaceWarning(ValidationWarning):
    ...
