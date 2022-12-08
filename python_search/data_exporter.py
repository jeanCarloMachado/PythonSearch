from python_search.config import ConfigurationLoader
from python_search.data_ui.homepage import extract_value_from_entry


class DataExporter:
    def export_as_text(self):
        entries = ConfigurationLoader().load_entries()


        data = ''
        for key, value in entries.items():
            serializeable_value = extract_value_from_entry(value)
            data = data + f"{key}={serializeable_value}\n"

        with open("exported_entries.txt", "w") as f:
            f.write(data)


if __name__ == "__main__":
    import fire
    fire.Fire()
