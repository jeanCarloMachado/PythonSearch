

class Preview:
    def display(self, entry_text):
        key = entry_text.split(':')[-1]
        json_str = entry_text.replace(key + ':', '')
        import json

        try:
            data = json.loads(json_str)
            print(json.dumps(data, indent=1))
        except:
            print(json_str)
