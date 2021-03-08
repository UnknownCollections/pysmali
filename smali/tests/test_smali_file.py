import io
import os
import tarfile
import unittest
import warnings
from typing import List

from smali import SmaliFile
from smali.block import Block
from smali.exceptions import ValidationError
from smali.statements import Statement, MethodStatement, FieldStatement


class TestSmaliFiles(unittest.TestCase):
    archive: tarfile.TarFile
    files: List[tarfile.TarInfo]

    def setUp(self):
        SmaliFile.VALIDATE = True
        Statement.VALIDATE = True
        cwd = os.path.abspath(os.path.dirname(__file__))
        tar_input_path = os.path.join(cwd, 'tests.tar.xz')
        self.archive = tarfile.open(tar_input_path)
        self.files = self.archive.getmembers()

    def tearDown(self):
        SmaliFile.VALIDATE = False
        Statement.VALIDATE = False
        self.archive.close()

    def test_parsing(self):
        for file in self.files:
            real_path = file.pax_headers.get('real_path')
            with self.subTest(name=file.name, real_path=real_path):
                with io.TextIOWrapper(self.archive.extractfile(file)) as f:
                    file_data = f.read()
                    try:
                        with warnings.catch_warnings(record=True) as w:
                            SmaliFile(file_data)
                            if w is not None and len(w) > 0:
                                self.fail('\n'.join(map(str, w)))
                    except ValidationError as e:
                        self.fail(e)
                    except Exception as e:
                        self.fail(e)

    def test_find(self):
        target = self.files[0]
        with io.TextIOWrapper(self.archive.extractfile(target)) as f:
            file_data = f.read()
            smali_file = SmaliFile(file_data)
            found = smali_file.find(MethodStatement, member_name='<init>', method_params='', method_result_type='V')
            self.assertEqual(len(found), 1)
            self.assertIsInstance(found[0], Block)
            self.assertIsInstance(found[0].head, MethodStatement)

    def test_find_methods(self):
        target = '00af6b80387134e695624faa23efbd603e4a58985e5a8d9f4c26bd6f069ce852.smali'
        with io.TextIOWrapper(self.archive.extractfile(target)) as f:
            file_data = f.read()
            smali_file = SmaliFile(file_data)
            found = smali_file.find_methods('checkCustomTabRedirectActivity')
            self.assertEqual(len(found), 2)
            self.assertIsInstance(found[0], Block)
            self.assertIsInstance(found[0].head, MethodStatement)
            self.assertMultiLineEqual('checkCustomTabRedirectActivity', found[0].head.member_name)
            self.assertMultiLineEqual('Landroid/content/Context;', found[0].head.method_params)
            self.assertMultiLineEqual('V', found[0].head.method_result_type)
            self.assertIsInstance(found[1], Block)
            self.assertIsInstance(found[1].head, MethodStatement)
            self.assertMultiLineEqual('checkCustomTabRedirectActivity', found[1].head.member_name)
            self.assertMultiLineEqual('Landroid/content/Context;Z', found[1].head.method_params)
            self.assertMultiLineEqual('V', found[1].head.method_result_type)

    def test_find_method(self):
        target = '00af6b80387134e695624faa23efbd603e4a58985e5a8d9f4c26bd6f069ce852.smali'
        with io.TextIOWrapper(self.archive.extractfile(target)) as f:
            file_data = f.read()
            smali_file = SmaliFile(file_data)
            found = smali_file.find_method('checkCustomTabRedirectActivity', '(Landroid/content/Context;Z)V')
            self.assertIsNotNone(found)
            self.assertIsInstance(found, Block)
            self.assertIsInstance(found.head, MethodStatement)
            self.assertEqual(26, len(found.items))
            self.assertMultiLineEqual('checkCustomTabRedirectActivity', found.head.member_name)
            self.assertMultiLineEqual('Landroid/content/Context;Z', found.head.method_params)
            self.assertMultiLineEqual('V', found.head.method_result_type)

    def test_find_field(self):
        target = '00af6b80387134e695624faa23efbd603e4a58985e5a8d9f4c26bd6f069ce852.smali'
        with io.TextIOWrapper(self.archive.extractfile(target)) as f:
            file_data = f.read()
            smali_file = SmaliFile(file_data)
            found = smali_file.find_field('NO_INTERNET_PERMISSION_REASON')
            self.assertIsNotNone(found)
            self.assertIsInstance(found, FieldStatement)
            self.assertMultiLineEqual('NO_INTERNET_PERMISSION_REASON', found.member_name)
            self.assertMultiLineEqual('Ljava/lang/String;', found.type_descriptor)


if __name__ == '__main__':
    unittest.main()
