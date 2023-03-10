from python_search.chat_gpt import ChatGPT


class EntryGenerator:

    def __init__(self):
        self._chat_gpt = ChatGPT()


    def generate_body(self, entry_description, body_size=500):
        prompt = f"""generate a command body following the pattern:
write python executable in screen to debug: import sys ; st.write(sys.executable)
pandas str expression to deal with string columns example: suburb_D = df[df.Suburb.str.startswith("D")] suburb_D.head()
conda enviroment folder: /Users/jean.machado/anaconda3/envs/
create databricks connect conda: conda env create -f environment.py.yml
zusatz: additive
ceo of open ai: Sam Altman
erfassen: capture
open ai documentation: https://platform.openai.com/docs/introduction
{entry_description}: 
        """

        return self._chat_gpt.answer(prompt, max_tokens=body_size)


if __name__ == "__main__":

    import fire
    fire.Fire(EntryGenerator())
