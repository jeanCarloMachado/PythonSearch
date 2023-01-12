import datetime
from python_search.events.run_performed.dataset import EntryExecutedDataset

def test_events_still_being_produced():
    """
    Asserts that we are producing events (having at least one produced today)
    """
    import pyspark.sql.functions as F

    df = EntryExecutedDataset().load_new()
    df = df.withColumn("datetime", F.from_unixtime("timestamp"))
    max_date = df.agg({"datetime": "max"}).collect()[0][0]
    assert datetime.date.today().isoformat().split(' ')[0] == max_date.split(' ')[0]
