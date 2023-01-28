import datetime
import pytest
import os


def in_ci():
    in_ci = "CI" in os.environ

    if in_ci:
        print("Running in CI")
    else:
        print("Not running in CI")

    return in_ci


@pytest.mark.skipif(in_ci(), reason="cant run in CI atm")
def test_events_still_being_produced():
    """
    Asserts that we are producing events (having at least one produced today)
    """
    from python_search.events.run_performed.dataset import EntryExecutedDataset
    import pyspark.sql.functions as F

    df = EntryExecutedDataset().load_new()
    df = df.withColumn("datetime", F.from_unixtime("timestamp"))
    max_date = df.agg({"datetime": "max"}).collect()[0][0]
    assert datetime.date.today().isoformat().split(" ")[0] == max_date.split(" ")[0]
