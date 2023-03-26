import os
from python_search.error.exception import notify_exception


class ChatGPT:
    """
    Uses OpenAI to answer a given prompt.
    """

    MODEL_ENGINE = "text-davinci-003"

    def __init__(self, max_tokens=500):
        self.max_tokens = int(max_tokens)

    def collect_prompt_via_ui(self):
        """
        Collects a prompt from the user via a UI.

        :return:
        """
        from python_search.apps.collect_input import CollectInput

        message = CollectInput().launch()
        self.answer(message)

    def given_prompt_plus_clipboard(self, given_prompt, return_promt=True):
        """
        Appends clipboard content to the given prompt and returns a string with the result.

        :param given_prompt:
        :return:
            str: A string with the result of combining the prompt with clipboard content.
        """

        from python_search.apps.clipboard import Clipboard

        content = Clipboard().get_content()

        prompt = f"{given_prompt}: {content}"
        result = self.answer(prompt)

        prompt_str = f"""
-------
Prompt:
{prompt}
"""

        if return_promt:
            result = f"""
{result}

{prompt_str}
            """
        else:
            result

        print(result)

    @notify_exception()
    def answer(self, prompt: str, debug=False, max_tokens=500, model=None):
        """
        Answer a prompt with openAI results
        """
        if len(prompt) > 4097:
            prompt = prompt[:4097]
        self.max_tokens= int(max_tokens)

        import openai

        openai.api_key = os.environ["OPENAI_KEY"]
        # Set the maximum number of tokens to generate in the response

        if debug:
            print("Prompt: ", prompt)

        engine = self.MODEL_ENGINE
        if model is not None:
            engine = None

        # Generate a response
        completion = openai.Completion.create(
            model=model,
            engine=engine,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=0.5,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        # Print the response
        return completion.choices[0].text.strip()

    def print_answer(self, prompt):
        print(self.answer(prompt))


def main():
    import fire

    fire.Fire(ChatGPT)


if __name__ == "__main__":
    main()
