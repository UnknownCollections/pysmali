import glob
import hashlib
import os
import tarfile


def main():
    cwd = os.path.join(os.path.dirname(__file__), 'src')
    glob_path = os.path.join(cwd, '**', '*.smali')
    tar_output_path = os.path.join(os.path.dirname(__file__), 'tests.tar.xz')

    with tarfile.open(tar_output_path, 'w:xz', format=tarfile.PAX_FORMAT) as archive:
        created_files = set(archive.getnames())
        for file in glob.iglob(glob_path, recursive=True):
            print(f'Adding {file}...')
            with open(file, 'r') as f:
                new_file_name = hashlib.sha256(f.read()).hexdigest()
                if new_file_name in created_files:
                    print('\t...file already added')
                created_files.add(new_file_name)
                new_file_info = archive.gettarinfo(fileobj=f, arcname=f'{new_file_name}.smali')
                new_file_info.pax_headers = {'real_path': os.path.relpath(file, cwd).replace('\\', '/')}
                f.seek(0)
                archive.addfile(new_file_info, f)


if __name__ == '__main__':
    main()
