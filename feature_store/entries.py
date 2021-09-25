# This is an example feature definition file
from datetime import timedelta

from feast import Entity, Feature, FeatureView, FileSource, ValueType

from search_run.data_paths import DataPaths

entries = FileSource(
    path=DataPaths.entries_dump_file,
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created",
)

# Define an entity for the driver. You can think of entity as a primary key used to
# fetch features.
entry = Entity(
    name="key",
    value_type=ValueType.STRING,
    description="The name of the dictionary key in search run",
)

# Our parquet files contain sample data that includes a driver_id column, timestamps and
# three feature column. Here we define a Feature View that will allow us to serve this
# data to our model online.
entries_snapshot = FeatureView(
    name="entries_snapshot",
    entities=["key"],
    features=[
        Feature(name="position", dtype=ValueType.INT32),
        Feature(name="key_lenght", dtype=ValueType.INT32),
    ],
    batch_source=entries,
    ttl=timedelta(days=365),
)
