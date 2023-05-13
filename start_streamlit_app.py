

def main():
    import os
    base_dir = os.path.dirname(os.path.realpath(__file__))
    os.system(f"cd {base_dir} ; PS_DISABLE_PASSWORD=True streamlit run python_search/web_ui/main.py ")