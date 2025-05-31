Set-Location "C:\Users\Admin\Documents\GitHub\discord-slash-bot"

& "C:\Users\Admin\Documents\GitHub\discord-slash-bot\.venv\Scripts\Activate.ps1"

python.exe -m pip install --upgrade pip

python.exe -m pip install discord.py python-dotenv Pillow PyNaCl sqlalchemy psycopg2

python.exe main.py