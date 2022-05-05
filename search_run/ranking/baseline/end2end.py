#!/usr/bin/env python
import logging
import sys

import pandas as pd

from search_run.observability.logger import initialize_logging
from search_run.ranking.baseline.serve import RankCache
from search_run.ranking.baseline.train import (aggregate_searches,
                                               compute_embeddings_current_keys,
                                               create_dataset, create_Y,
                                               load_searches,
                                               perform_train_and_log,
                                               validate_latest_model_ranks)

initialize_logging()


class EndToEnd:
    def run(self):
        X, Y = self.create_dataset()
        keys_embeddings = compute_embeddings_current_keys()

        perform_train_and_log(keys_embeddings, X, Y)
        self.validate()
        self.clear_cache()

    def create_dataset(self):
        searches_df = load_searches()
        aggreagted_df = aggregate_searches(searches_df)
        X = create_dataset(aggreagted_df)
        Y = create_Y(aggreagted_df)
        print(X)

        return X, Y

    def clear_cache(self):
        RankCache().clear()

    def validate(self):
        result: pd.DataFrame = validate_latest_model_ranks()
        print(result.head(n=30))


if __name__ == "__main__":
    import fire

    fire.Fire(EndToEnd)
