import os


os.system("rm -rf dist/*")
os.system("rm -rf __pycache__")
os.system("rm -rf .mypy_cache")

os.system("black . ")
