curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc
export PATH="/root/.local/bin:$PATH"
poetry install -E server
apt-get update -y
apt install default-jre -y