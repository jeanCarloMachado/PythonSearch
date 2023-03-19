import json
import sys

from python_search.chat_gpt import ChatGPT
from python_search.error.exception import notify_exception


class EntryGenerator:

    def __init__(self):
        self._chat_gpt = ChatGPT()


    def generate_body(self, prompt, body_size=500, fine_tune=False):
        if fine_tune:
            prompt = f"""generate a command body following the pattern: name: content | Type (one of the following snippet, cli_cmd, url, file)
write python executable in screen to debug: import sys ; st.write(sys.executable) | snippet
pandas str expression to deal with string columns example: suburb_D = df[df.Suburb.str.startswith("D")] suburb_D.head() | file
conda enviroment folder: /Users/jean.machado/anaconda3/envs/ | file
create databricks connect conda: conda env create -f environment.py.yml | cli_cmd
zusatz: additive | snippet
ceo of open ai: Sam Altman | snippet
erfassen: capture | snippet
open ai documentation: https://platform.openai.com/docs/introduction | url
{prompt}: 
            """

        return self._chat_gpt.answer(prompt, max_tokens=body_size)

    @notify_exception()
    def fzf_formatted(self, query):
        import os
        os.system(f"echo '{query}'>> /tmp/query_log")
        SECONDS_TO_WAIT = 1.3
        import time;  time.sleep(SECONDS_TO_WAIT)

        # if after 3 seconds teh last query is the same we then can continue to query it
        with open("/tmp/query_log", "r") as f:
            last_query = f.readlines()[-1].strip()
            if last_query.strip() != query.strip():
                print("Wont continue due ot last query not being the same as the current one")
                sys.exit(1)



        result = self.generate_body(query, body_size=500, fine_tune=True)


        type = result.split('|')[-1]
        content = result[0:-len(type) - 1]
        content = content.strip()
        type = type.strip()


        dict = {
            type: content,
        }

        return f"""{query}                                           : {json.dumps(dict)}"""


def main():
    import fire
    fire.Fire(EntryGenerator())

if __name__ == "__main__":
    main()
