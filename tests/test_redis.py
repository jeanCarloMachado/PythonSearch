from search_run.events.latest_used_entries import LatestUsedEntries

test_redis_key_name = "test_last_consumed_keys"


def test_write_to_redis():
    LatestUsedEntries(key_name=test_redis_key_name).write_last_used_key(
        "enable_sentry_remote_mode"
    )


def test_read_from_redis():
    result = LatestUsedEntries().get_latest_used_keys()

    return result


if __name__ == "__main__":
    import fire

    fire.Fire()
