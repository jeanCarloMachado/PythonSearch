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

        sensitive_entries = 0
        for entry in entries:
            for term in self.configuration.privacy_sensitive_terms:
                if term in entry.key or term in entry.get_content_str():
                    print("Found sensitive term: ", term, " in entry: ", entry.key)
                    sensitive_entries += 1
        print("Found ", sensitive_entries, " sensitive entries")



if __name__ == "__main__":
    import fire
    fire.Fire(Detector)
