from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Entry


class DataExporter:
    MAX_LENGTH = 100

    def __init__(self):
        import os

        extra_excluded_terms = os.environ.get("PYTHON_SEARCH_EXCLUDE_EXPORT", "")
        if extra_excluded_terms:
            print("Adding extra excluded terms: ", extra_excluded_terms)
            self.blacklisted_terms.extend(extra_excluded_terms.split(" "))

    def filter_out_blacklisted(self, entries):
        result = {}
        for key, value in entries.items():
            entry = Entry(key, value)
            content = entry.get_content_str()
            serializeable_value = content.replace("\n", " ")

            if serializeable_value.strip() == "":
                continue

            if len(serializeable_value) > self.MAX_LENGTH:
                continue

            if any(
                [
                    blackelisted_entry in key.lower()
                    for blackelisted_entry in self.blacklisted_terms
                ]
            ):
                print("Skipping blacklisted key: ", key)
                continue

            if any(
                [
                    blackelisted_entry in serializeable_value.lower()
                    for blackelisted_entry in self.blacklisted_terms
                ]
            ):
                print("Skipping blacklisted value: ", serializeable_value)
                continue

            if "private" in value:
                continue

            result[key] = serializeable_value

        return result

    def export_as_text(self):
        entries = ConfigurationLoader().load_entries()

        data = ""
        entries = self.filter_out_blacklisted(entries)
        for key, value in entries.items():
            entry = Entry(key, value)
            content = entry.get_content_str()
            data = data + f"{key}={content}\n"

        with open("exported_entries.txt", "w") as f:
            f.write(data)


if __name__ == "__main__":
    import fire

    fire.Fire()
