import sys
import os
from cx_Freeze import setup, Executable
import distutils
import site


# Find PyWin32 directory
pywin32_path = None
for path in site.getsitepackages():
    possible_path = os.path.join(path, 'pywin32_system32')
    if os.path.exists(possible_path):
        pywin32_path = possible_path
        break

# Find additional DLLs needed
dll_files = []
if pywin32_path:
    dll_files = [(os.path.join(pywin32_path, file), file) for file in os.listdir(pywin32_path) 
                 if file.lower().endswith('.dll')]


if __name__ == '__main__':
    setup(
        name='common_clipboard',
        description='Common Clipboard',
        author='cmdvmd',
        version='1.1b3',
        options={
            'build_exe': {
                'packages': [
                    'setuptools',
                    'requests',
                    'time',
                    'win32clipboard',
                    'sys',
                    'os',
                    'pickle',
                    'socket',
                    'threading',
                    'multiprocessing',
                    'enum',
                    'pystray',
                    'PIL',
                    'io',
                    'ntplib',
                    'flask',
                    'tkinter'
                ],
                'excludes': [
                    '_distutils_hack',
                    'asyncio'
                    'concurrent',
                    'distutils',
                    'lib2to3',
                    'pkg_resources',
                    'pydoc_data',
                    'test',
                    'unittest',
                    'xml',
                    'xmlrpc',
                ],
                'include_files': [
                    'systray_icon.ico'
                ] + dll_files,
                'optimize': 2,
                'include_msvcr': True,  # Include MSVC runtime files
                'zip_include_packages': "*",
                'zip_exclude_packages': "",
            }
        },
        executables=[
            Executable(
                script='common_clipboard.py',
                icon='../static/icon.ico',
                copyright='Copyright (c) cmdvmd 2023',
                base='Win32GUI' if sys.platform == 'win32' else None
            )
        ]
    )
