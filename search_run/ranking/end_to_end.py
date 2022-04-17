#!/usr/bin/env python
import logging
import sys

from search_run.ranking.pipeline.train import validate_latest_model_ranks

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]),


class EndToEnd:
    def run(self):
        from sklearn.model_selection import train_test_split

        from search_run.ranking.pipeline.train import (
            aggregate_searches, compute_embeddings_current_keys,
            create_dataset, create_Y, load_searches, perform_train_and_log)

        searches_df = load_searches()
        aggreagted_df = aggregate_searches(searches_df)
        X = create_dataset(aggreagted_df)
        Y = create_Y(aggreagted_df)

        keys_embeddings = compute_embeddings_current_keys()

        # Splitting
        train_X, test_X, train_y, test_y = train_test_split(
            X, Y, test_size=0.2, random_state=223
        )

        perform_train_and_log(keys_embeddings, train_X, train_y, test_X, test_y)

    def validate(self):
        return validate_latest_model_ranks()


if __name__ == "__main__":
    import fire

    fire.Fire(EndToEnd)
