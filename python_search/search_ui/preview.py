class Preview:
    def display(self, entry_text):
        """
        Prints the
        """
        key = entry_text.split(":")[0]
        json_str = entry_text.replace(key + ":", "")
        import json

        try:
            data = json.loads(json_str)
            print(json.dumps(data, indent=1))
        except BaseException as e:
            print(json_str)
