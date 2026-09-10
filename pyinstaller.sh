pyinstaller --onefile --name miaospeed-web --add-binary "miaospeed-windows-amd64.exe;." --add-data "front/out;front/out" --add-data "scripts;scripts" --hidden-import miaospeedlib main.py
