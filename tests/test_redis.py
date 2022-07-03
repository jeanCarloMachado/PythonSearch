import os

import pytest

from search_run.events.latest_used_entries import LatestUsedEntries

test_redis_key_name = "test_last_consumed_keys"


@pytest.mark.skipif("CI" in os.environ, reason="not supported on ci yet")
def test_write_to_redis():
    LatestUsedEntries(key_name=test_redis_key_name).write_last_used_key(
        "enable_sentry_remote_mode"
    )


@pytest.mark.skipif("CI" in os.environ, reason="not supported on ci yet")
def test_read_from_redis():
    result = LatestUsedEntries().get_latest_used_keys()

    return result


if __name__ == "__main__":
    import fire

    fire.Fire()
