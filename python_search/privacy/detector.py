from python_search.search.entries_loader import EntriesLoader


class Detector:

    def __init__(self):
        from python_search.configuration.loader import ConfigurationLoader;
        self.configuration = ConfigurationLoader().load_config()

    def detect_in_entries(self):

        if not self.configuration.privacy_sensitive_terms:
            print("No sensitive terms configured")
            return

        entries = EntriesLoader.load_entry_list()

        the_list = []
        for entry in entries:
            the_list.append(entry.key)
            the_list.append(entry.get_content_str())
        self.detect_in_list(the_list)

    def detect_in_list(self, data):
        sensitive_entries = 0
        total_entries = 0
        for entry in data:
            for term in self.configuration.privacy_sensitive_terms:
                if term in entry:
                    print("Found sensitive term: ", term, " in entry: ", entry)
                    sensitive_entries += 1
            total_entries += 1
        print("Found ", sensitive_entries, " sensitive entries in a total of ", total_entries, " entries")



if __name__ == "__main__":
    import fire
    fire.Fire(Detector)
