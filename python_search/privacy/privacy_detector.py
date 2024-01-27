from typing import List, Tuple


class PrivacyDetector:
    def __init__(self):
        from python_search.configuration.loader import ConfigurationLoader

        self.configuration = ConfigurationLoader().load_config()

    def has_sentitive_content(self, the_string) -> bool:
        return self.get_sensitive_content(the_string)[0]

    def get_sensitive_content(self, the_string) -> Tuple[bool, str]:
        for term in self.configuration.privacy_sensitive_terms:
            if term in the_string:
                return True, term
        return False, None

    def detect_in_list(self, data: List[str]):
        sensitive_entries = 0
        total_entries = 0
        for entry in data:
            is_sensitive, term = self.get_sensitive_content(entry)
            if is_sensitive:
                print(f"Found {term} in string: {entry[0:100]}")
                sensitive_entries += 1
            total_entries += 1
        print(
            "Found ",
            sensitive_entries,
            " sensitive entries in a total of ",
            total_entries,
            " entries",
        )


if __name__ == "__main__":
    import fire

    fire.Fire(PrivacyDetector)
