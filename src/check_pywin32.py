import os
import site
import sys

def find_pywin32_dlls():
    """Find all PyWin32 DLLs in the Python installation."""
    pywin32_dlls = []
    
    # Check standard site-packages locations
    for path in site.getsitepackages():
        # Check pywin32_system32 folder
        pywin32_system32 = os.path.join(path, 'pywin32_system32')
        if os.path.exists(pywin32_system32):
            print(f"Found pywin32_system32 directory: {pywin32_system32}")
            for file in os.listdir(pywin32_system32):
                if file.lower().endswith('.dll'):
                    pywin32_dlls.append(os.path.join(pywin32_system32, file))
        
        # Check win32 folder
        win32_dir = os.path.join(path, 'win32')
        if os.path.exists(win32_dir):
            print(f"Found win32 directory: {win32_dir}")
            for file in os.listdir(win32_dir):
                if file.lower().endswith('.pyd'):
                    pywin32_dlls.append(os.path.join(win32_dir, file))
    
    return pywin32_dlls

if __name__ == "__main__":
    dlls = find_pywin32_dlls()
    print(f"Found {len(dlls)} PyWin32 DLL/PYD files:")
    for dll in dlls:
        print(f" - {dll}")
    
    print("\nAdd these to your setup.py include_files list.")