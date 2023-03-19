from python_search.chat_gpt import ChatGPT
from python_search.error.exception import notify_exception


class EntryGenerator:

    def __init__(self):
        self._chat_gpt = ChatGPT()


    def generate_body(self, prompt, body_size=500, fine_tune=False):
        if fine_tune:
            prompt = f"""generate a command body following the pattern: name: content | Type (one of the following Snippet, Cmd, Url, File)
write python executable in screen to debug: import sys ; st.write(sys.executable) | Snippet
pandas str expression to deal with string columns example: suburb_D = df[df.Suburb.str.startswith("D")] suburb_D.head() | File
conda enviroment folder: /Users/jean.machado/anaconda3/envs/ | File
create databricks connect conda: conda env create -f environment.py.yml | Cmd
zusatz: additive | Snippet
ceo of open ai: Sam Altman | Snippet
erfassen: capture | Snippet
open ai documentation: https://platform.openai.com/docs/introduction | Url
{prompt}: 
            """

        return self._chat_gpt.answer(prompt, max_tokens=body_size)

    @notify_exception()
    def fzf_formatted(self, query):
        return ""
        result = self.generate_body(query, body_size=500, fine_tune=True)

        type = result.split('|')[-1]
        content = result[0:-len(type) - 1]
        content = content.strip()
        type = type.strip()


        dict = {
            type: content,
        }

        return f"""{query}: {dict}"""


def main():
    import fire
    fire.Fire(EntryGenerator())

if __name__ == "__main__":
    main()
