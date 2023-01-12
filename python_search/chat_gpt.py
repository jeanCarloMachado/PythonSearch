import openai
import os

openai.api_key = os.environ["OPENAI_KEY"]
model_engine = "text-davinci-003"

class ChatGPT:
    def collect_prompt_via_ui(self):
        from python_search.apps.collect_input import CollectInput
        message = CollectInput().launch()
        self.answer(message)

    def answer(self, prompt):

        # Set the maximum number of tokens to generate in the response
        max_tokens = 500
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
