from datetime import timedelta

from feast import Entity, Feature, FeatureView, FileSource, ValueType

from search_run.data_paths import DataPaths

entries = FileSource(
    path=DataPaths.entries_dump_file,
    event_timestamp_column="event_timestamp",
)

entry = Entity(
    name="entry_key",
    value_type=ValueType.STRING,
    description="The name of the dictionary key in search run",
)

entries_snapshot = FeatureView(
    name="entries_snapshot",
    entities=["entry_key"],
    features=[
        Feature(name="position", dtype=ValueType.INT32),
        Feature(name="key_lenght", dtype=ValueType.INT32),
    ],
    batch_source=entries,
    ttl=timedelta(days=365),
)
