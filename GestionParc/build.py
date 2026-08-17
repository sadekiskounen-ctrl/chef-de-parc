import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = 'SARL_NOMADE_Ayris'
assets_dir = ROOT / 'assets'
icon_path = assets_dir / 'ayris.ico'
if not icon_path.exists():
    icon_path = assets_dir / 'logo_nomade_ayris.png'

pyinstaller_cmd = [
    sys.executable,
    '-m',
    'PyInstaller',
    '--onefile',
    '--noconsole',
    '--name',
    APP_NAME,
    '--add-data',
    f"{assets_dir}{os.pathsep}assets",
    '--icon',
    str(icon_path),
    str(ROOT / 'main.py')
]

print('Commande build :')
print(' '.join(pyinstaller_cmd))

res = subprocess.run(pyinstaller_cmd, cwd=str(ROOT))
if res.returncode == 0:
    print(f'\nBuild réussi ! Le binaire est généré dans {ROOT / "dist" / (APP_NAME + ".exe")}')
else:
    print(f'\nErreur lors du build (code {res.returncode}).')
    sys.exit(res.returncode)

