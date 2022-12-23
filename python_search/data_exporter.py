from python_search.config import ConfigurationLoader
from python_search.data_ui.entries_page import extract_value_from_entry


class DataExporter:
    blacklisted_terms = [
        "http://",
        "https://",
        "email",
        "no key ",
        "insurance",
        "token",
        "private",
        "endereco",
        "password",
        "secret",
        "passport",
        "passaporte",
        "telefone",
        "phone",
        "celular",
        "cellphone",
        "cpf",
    ]

    def export_as_text(self):

        entries = ConfigurationLoader().load_entries()

        data = ""
        for key, value in entries.items():
            serializeable_value = extract_value_from_entry(value).replace("\n", " ")
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

            data = data + f"{key}={serializeable_value}\n"

        with open("exported_entries.txt", "w") as f:
            f.write(data)


if __name__ == "__main__":
    import fire

    fire.Fire()
