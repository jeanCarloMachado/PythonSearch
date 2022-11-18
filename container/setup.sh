#!/bin/bash

# poetry setup
#curl -sSL https://install.python-poetry.org | python3 -
#export PATH="/root/.local/bin:$PATH"
#poetry config virtualenvs.create false

# conda installation
export PATH="/root/miniconda3/bin/:$PATH"

dpkg --print-architecture | grep "arm64"
if [[ $? -eq 0  ]]; then
  echo "Arm architecture detected"
  FILE_NAME=Miniconda3-py39_4.12.0-Linux-aarch64.sh
else
  echo "AMD architecture detected"
  FILE_NAME=Miniconda3-py39_4.12.0-Linux-x86_64.sh
fi

wget https://repo.anaconda.com/miniconda/$FILE_NAME
chmod +x $FILE_NAME
./$FILE_NAME -b -f
#conda init bash
conda create -n 310 python=3.10
export PATH="/root/miniconda3/envs/310/bin/:$PATH"
pip install poetry
pip install nvidia-pyindex
#conda run --no-capture-output -n 310 poetry install
