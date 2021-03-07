# PySmali

PySmali is a Python library for parsing and unparsing smali files for programatic modification. 

It is a line *(not token)* based parser. Its primary goal is for parsed files to maintain 100% equality with their original forms when reconstructed.

PySmali's main usage is for smali file patching. You are able to parse, search, extract, replace, and unparse blocks of a smali file.

Parsing is based on the ANTLR files found in the [JesusFreke/smali](https://github.com/JesusFreke/smali) repository. 

Since this is a line, and not token, based parser, there are likely to be edge cases where PySmali fails to properly parse or unparse a file. There are currently 6,846 smali files that are used in the `tests` folder (`tests/tests.tar.xz`). 

If you run into a smali file that does not parse or unparse properly, please submit a [new issue](https://github.com/UnknownCollections/pysmali/issues/new) with the complete smali file(s) attached as a `zip` or `gz` archive.

## Requirements

* Python 3.8 or newer

## Installation

```bash
pip install smali
```

## Simple Example

```python
import time
from smali import SmaliFile
from smali.statements import Statement

smali_file = SmaliFile.parse_file('/path/to/file.smali')

new_lines = Statement.parse_lines(f'''
# This file was modified by PySmali
# Modified: {time.ctime()}
''')

smali_file.root.extend(new_lines)

with open('/path/to/file.smali', 'w') as f:
    f.write(str(smali_file))
```

## Status
  
- **[UPCOMING] v0.4.0**
  - Complete parsing of body statements
  
- **[UPCOMING] v0.3.0**
  - `Statement` and `Block` searching by method and field names
  - Simplified `Statement` and `Block` extraction and insertion

- **v0.2.5**
  - Removed all dependencies and reorganized utility code

- **v0.2.4**
  - Complete parsing and unparsing of non-body statements validated by current test suite
  
## Methodology

- The smali file is ingested on a line by line basis
- Each line is parsed into one or more `Statement` instances
  - `.super Ljava/lang/Object;` would become a single `Statement` instance
  - `value = { LFormat31c; }` would become 4 `Statement` instances
    - `value`, `{`, `LFormat31c;`, `}`
- Each `Statement` instance is subclassed based on its type
  - E.g. `FieldStatement` or `MethodStatement`
- A `Statement` can have zero or more `StatementAttributes` that indicate its intent and format
  - E.g. `BLOCK_START`, `ASSIGNMENT_LHS`, or `NO_BREAK`
- Multiple `Statement` instances can be joined into a `Block` and nested where appropriate
  - A `Block` example would be a smali method, comprised of beginning, body, and end `Statement` instances
- A `Statement` parses its source line, split by whitespace
- Parsing is done in two passes. This is due to the fact that the same line can be the start of a block, or a solo line depending on the existence of a matching `EndStatement`.
  - The first pass builds a flat list of `Statement` instances from the input lines. 
  - A `Statement` that can be either a `Block` start or a solo line is marked with the `MAYBE_BLOCK_START` attribute
  - If an `EndStatement` is generated, and matches a previously marked `Statement`, the marked `Statement` is switched from `MAYBE_BLOCK_START` to `BLOCK_START`.
  - After the first pass, any remaining `Statement` instances that are still marked with `MAYBE_BLOCK_START` are switched to `SINGLE_LINE`,
  - The second pass iterates over the flat list of `Statement` instances and groups them into `Block` instances and nesting when appropriate based on the `SINGLE_LINE` and `BLOCK_START` attributes.
- Unparsing is done in a single pass
  - Each `Statement` stringifies itself using its own local information
  - The `SmaliFile` instance uses the attributes of each `Statement` to stitch lines together and indent blocks where necessary

## License

[UNLICENSE](https://unlicense.org/)

## OSS Attribution

### [JesusFreke/smali](https://github.com/JesusFreke/smali) by **Ben Gruver**
_Licensed Under: [Various Licenses](https://github.com/JesusFreke/smali/blob/master/NOTICE)_

### Tests

Smali files used as tests in the `tests/tests.tar.xz` archive have been obtained from the following projects:
- Android
- AndroidX
- Facebook
- FasterXML
- Google
- Java
- JavaX
- OkHttp
- Smali