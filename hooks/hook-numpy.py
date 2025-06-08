# hooks/hook-numpy.py
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# garante que todos os submódulos C e pacotes de dados serão incluídos
hiddenimports = collect_submodules('numpy')
datas = collect_data_files('numpy', include_py_files=True)
