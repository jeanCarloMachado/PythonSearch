import json
import sys
import os
import time

from python_search.chat_gpt import LLMPrompt
from python_search.error.exception import notify_exception


class EntryGenerator:
    def __init__(self):
        self._chat_gpt = LLMPrompt()
        from python_search.configuration.loader import ConfigurationLoader

        self.configuration = ConfigurationLoader().load_config()

    def generate_body(
        self, *, prompt, max_tokens=500, fine_tuned=False, few_shot=False, model=None
    ):
        if few_shot:
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

        if fine_tuned:
            model = "curie:ft-jean-personal-2023-03-20-21-40-47"

        return self._chat_gpt.answer(prompt, max_tokens=max_tokens, model=model)

    @notify_exception()
    def generate_for_fzf(self, query):
        if not self.configuration.entry_generation:
            # entry generation is disabled
            return

        os.system(f"echo '{query}'>> /tmp/query_log")
        SECONDS_TO_WAIT = 1.3
        time.sleep(SECONDS_TO_WAIT)

        # if after 3 seconds teh last query is the same we then can continue to query it
        with open("/tmp/query_log", "r") as f:
            last_query = f.readlines()[-1]
            if not last_query:
                sys.exit(0)
            last_query = last_query.strip()
            if last_query.strip() != query.strip():
                print(
                    "Wont continue due ot last query not being the same as the current one"
                )
                sys.exit(1)

        result = self.generate_body(prompt=query, few_shot=True)

        type = result.split("|")[-1]
        content = result[0 : -len(type) - 1]
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
