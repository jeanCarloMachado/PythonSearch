from typing import Literal

from python_search.chat_gpt import LLMPrompt



class TypeDetector:
    classifier = None

    def __init__(self):
        from python_search.ps_llm.tasks.classity_entry_type import ClassifyEntryType
        from python_search.configuration.loader import ConfigurationLoader;
        configuration = ConfigurationLoader().load_config()
        if configuration.is_rerank_via_model_enabled():
            self.classifier = ClassifyEntryType.start_with_model()
    def detect(self, key, content) -> Literal["Url", "Snippet", "File", "Cmd"]:
        if content.startswith("https://") or content.startswith("http://"):
            return "Url"

        if self.classifier:
            result = self.classifier.classify(key, content)
            return result

        return "Snippet"



    def _chat_gpt(self, key, content):
        prompt = f""" return one of the following types (Snippet, File, Cmd)
        example of mac short: "mac_shortcuts": ["⇧⌘K", "⌥W"],=Snippet
        update poetry inside python search: ps_container run --cmd 'poetry update'=Cmd
        titulo eleitoral file: /Users/jean.machado/Dropbox/Documents/titulo_eleitor.pdf=File
        list files installed by package brew: brew ls --verbose redis=Cmd
        {key} : {content} = 
        """

        result = LLMPrompt().answer(prompt, max_tokens=20)
        if result not in ["Snippet", "File", "Cmd"]:
            print("Failed to detect type, defaulting to Snippet")
            result = "Snippet"
        print("Chat gpt result: " + result)

        return result
