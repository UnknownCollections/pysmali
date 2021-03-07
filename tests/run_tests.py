import io
import os
import sys
import tarfile
import warnings
from typing import Dict, List, Optional, Set

from tqdm import tqdm

from smali import SmaliFile
from smali.exceptions import ValidationError, ValidationWarning
from smali.statements import Statement


def main(targets: Optional[Set[str]] = None):
    SmaliFile.VALIDATE = True
    Statement.VALIDATE = True

    cwd = os.path.abspath(os.path.dirname(__file__))
    tar_input_path = os.path.join(cwd, 'tests.tar.xz')

    validation_warnings: Dict[str, List[ValidationWarning]] = {}
    validation_errors: Dict[str, List[ValidationError]] = {}
    exceptions: Dict[str, List[Exception]] = {}

    print(f'Testing PySmali v{SmaliFile.__version__}')
    print('----------------------------')

    with tarfile.open(tar_input_path, 'r:xz') as archive:
        files_progress = tqdm(archive.getmembers(), desc='Testing smali files', unit='file', bar_format='{desc:>50}{percentage:3.0f}%|{bar:10}{r_bar}')
        for file in files_progress:
            real_path = file.pax_headers.get('real_path')

            if targets is not None and real_path not in targets:
                continue

            def catch_warnings(message, *__, **___):
                if real_path not in validation_warnings:
                    validation_warnings[real_path] = []
                validation_warnings[real_path].append(message)

            warnings.showwarning = catch_warnings

            files_progress.set_description(f'[W:{len(validation_warnings)}|E:{len(validation_errors)}|EX:{len(exceptions)}] {real_path[-30:]}')

            with io.TextIOWrapper(archive.extractfile(file)) as f:
                file_data = f.read()
                try:
                    SmaliFile(file_data)
                except ValidationError as e:
                    if real_path not in validation_errors:
                        validation_errors[real_path] = []
                    validation_errors[real_path].append(e)
                    if getattr(sys, 'gettrace', None) is not None:
                        raise
                except Exception as e:
                    if real_path not in exceptions:
                        exceptions[real_path] = []
                    exceptions[real_path].append(e)
                    if getattr(sys, 'gettrace', None) is not None:
                        raise

    print('----------------------------')
    print()
    print('PySmali Test Results')
    print('----------------------------')
    print()
    print(f'[WHITESPACE WARNINGS] {len(validation_warnings)} files have unmatching whitespace')
    print(f'[VALIDATION ERRORS] {len(validation_errors)} incorrectly parsed files')
    print(f'[PARSING EXCEPTIONS] {len(exceptions)} files unable to be parsed')
    print()
    print()

    if len(validation_warnings) > 0:
        print('[VALIDATION WARNINGS]')
        print()
        for file, warns in validation_warnings.items():
            print(f'{file}')
            for warn in warns:
                print(f'{warn}')
            print()
        print()

    if len(validation_errors) > 0:
        print('[VALIDATION ERRORS]')
        print()
        for file, errors in validation_errors.items():
            print(f'{file}')
            for error in errors:
                print(f'{error}')
            print()
        print()

    if len(exceptions) > 0:
        print('[PARSING EXCEPTIONS]')
        print()
        for file, errors in exceptions.items():
            print(f'{file}')
            for error in errors:
                print(f'{error}')
            print()
        print()


if __name__ == '__main__':
    main()
