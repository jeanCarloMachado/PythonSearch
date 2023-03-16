from python_search.chat_gpt import ChatGPT


class TypeDetector():


    def detect(self, key, content):
        if content.startswith("http://") or content.startswith("http://"):
            return 'Url'

        prompt = f""" return one of the following types (Snippet, File, Cmd)
        example of mac short: "mac_shortcuts": ["⇧⌘K", "⌥W"],=Snippet
        update poetry inside python search: ps_container run --cmd 'poetry update'=Cmd
        titulo eleitoral file: /Users/jean.machado/Dropbox/Documents/titulo_eleitor.pdf=File
        list files installed by package brew: brew ls --verbose redis=Cmd
        {key} : {content} = 
        """

        result = ChatGPT().answer(prompt, max_tokens=20)
        if result not in ['Snippet', 'File', 'Cmd']:
            print('Failed to detect type, defaulting to Snippet')
            result = 'Snippet'
        print("Chat gpt result: " + result)

        return result