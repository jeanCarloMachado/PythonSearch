from datetime import datetime

import pandas as pd
from feast import FeatureStore

entity_df = pd.DataFrame.from_dict(
    {
        "entry_key": ["spotify music player"],
        "event_timestamp": [datetime.now()],
    }
)
store = FeatureStore(repo_path="feature_store")
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "entries_snapshot:position",
        "entries_snapshot:key_lenght",
    ],
).to_df()

print(training_df.info())
print(training_df.head())
