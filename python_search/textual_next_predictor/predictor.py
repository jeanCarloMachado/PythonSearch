from python_search.chat_gpt import ChatAPI
from python_search.events.latest_used_entries import RecentKeys
from python_search.logger import setup_inference_logger

class TextualPredictor:

    def __init__(self):
        self._logger = setup_inference_logger()

    def predict(self):
        recent = RecentKeys().get_latest_used_keys(history_size=100)
        recent_text = "\n".join(recent)
        prompt = f"""predict the most likely next action only using 50 characters max based on the following actions history sorted by most recent to least recent
{recent_text}
"""
        self._logger.debug("prompt", prompt)

        return ChatAPI().prompt(prompt)



def main():
    import fire

    fire.Fire(TextualPredictor)

if __name__ == "__main__":
    main()