import os


class ChatGPT:
    """
        Uses OpenAI to answer a given prompt.
    """
    def collect_prompt_via_ui(self):
        """
        Collects a prompt from the user via a UI.

        :return:
        """
        from python_search.apps.collect_input import CollectInput
        message = CollectInput().launch()
        self.answer(message)

    def given_prompt_plus_clipboard(self, given_prompt):
        """
        Appends clipboard content to the given prompt and returns a string with the result.

        :param given_prompt:
        :return:
            str: A string with the result of combining the prompt with clipboard content.
        """

        from python_search.apps.clipboard import Clipboard;
        content = Clipboard().get_content()

        prompt = f"{given_prompt}: {content}"
        result = self.answer(prompt)


        return f"""
Result:
        {result}





Prompt:
        {prompt}
        """

    def answer(self, prompt: str, debug=False):
        """
        Answer a prompt with openAI results
        """

        import openai
        openai.api_key = os.environ["OPENAI_KEY"]
        model_engine = "text-davinci-003"
        # Set the maximum number of tokens to generate in the response
        max_tokens = 500

        if debug:
            print("Prompt: ", prompt)

        # Generate a response
        try:
            completion = openai.Completion.create(
                engine=model_engine,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.5,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        except Exception as e:
            print(f"Error {e}")
            return ""

        # Print the response
        return completion.choices[0].text.strip()

    def print_answer(self, prompt):
        print(self.answer(prompt))

def main():
    import fire
    fire.Fire(ChatGPT)


if __name__ == "__main__":
    main()
