import hashlib
import re


class ValidationComparison:
    RE_FIND_COMMENTS = re.compile(r'(#.*)$', re.MULTILINE)
    RE_FIND_INDENTATION = re.compile(r'((^[ \t]+)|([ \t]+$))', re.MULTILINE)
    RE_FIND_OVERSIZED_WHITESPACE = re.compile(r'[\t ]{2,}')
    RE_FIND_EXTRA_NEWLINES = re.compile(r'[\t ]{2,}')

    @staticmethod
    def order_independent_hash(data: str) -> bytes:
        tokens = ''.join(sorted(filter(lambda x: not x.isspace(), list(data))))
        return hashlib.md5(tokens.encode()).digest()

    @staticmethod
    def normalize_smali(smali: str) -> str:
        smali = ValidationComparison.RE_FIND_COMMENTS.sub('', smali)
        smali = ValidationComparison.RE_FIND_INDENTATION.sub('', smali)
        smali = ValidationComparison.RE_FIND_OVERSIZED_WHITESPACE.sub(' ', smali)
        return ValidationComparison.RE_FIND_EXTRA_NEWLINES.sub('\n', smali)

    @staticmethod
    def whitespace_normalized_equals(a: str, b: str) -> bool:
        return ValidationComparison.normalize_smali(a) == ValidationComparison.normalize_smali(b)
