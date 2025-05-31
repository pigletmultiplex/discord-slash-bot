Set-Location "C:\Users\Admin\Documents\GitHub\discord-slash-bot"

# check remote repository
git fetch origin
if ($(git rev-parse HEAD) -ne $(git rev-parse origin/main)) {
    Write-Host "Pulling latest changes from remote repository..."
    git pull origin main
} else {
    Write-Host "Already up to date with remote repository."
}
# check if virtual environment exists
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
} else {
    Write-Host "Virtual environment already exists."
}
# Activate the virtual environment
if (-Not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment activation script not found."
    exit 1
}
& ".venv\Scripts\Activate.ps1"
# Upgrade pip and install required packages     
python -m pip install --upgrade pip
if (-Not (python -m pip show discord.py)) {
    Write-Host "Installing required packages..."
    python -m pip install discord.py python-dotenv Pillow PyNaCl sqlalchemy psycopg2
} else {
    Write-Host "Required packages already installed."
}
# Run the bot
Write-Host "Starting the bot..."
python main.py