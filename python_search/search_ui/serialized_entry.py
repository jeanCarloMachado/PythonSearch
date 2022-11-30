import json

def decode_serialized_data_from_entry_text(entry_text: str, logger=None) -> dict:
    key = entry_text.split(":")[0]
    serialized_content = entry_text[len(key) + 1:]
    try:
        return json.loads(serialized_content)
    except Exception as e:
        message = f"Failed with error {e} wile decoding the followingthe entry_text '{entry_text}' "
        if logger:
            logger.info(message)

        print(message)
        return {}
