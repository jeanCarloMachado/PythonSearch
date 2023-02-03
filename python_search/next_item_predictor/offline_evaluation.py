import pandas as pd
from pyspark.sql import DataFrame

import pprint
from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.configuration.loader import ConfigurationLoader
from python_search.logger import setup_generic_stdout_logger
from python_search.next_item_predictor.inference.inference import Inference
from python_search.next_item_predictor.inference.input import ModelInput


class OfflineEvaluation:
    """
    Evaluate the model with the validation set
    """

    _NUMBER_OF_TESTS = 100

    def __init__(self):
        self._configuration: PythonSearchConfiguration = (
            ConfigurationLoader().load_config()
        )

    def run_current_model(self, debug_row=False):
        model_class = self._configuration.get_next_item_predictor_model()
        model = model_class.load_mlflow_model()

        dataset = model_class.load_or_build_dataset()

        self.run(model, dataset.toPandas(), debug_row=debug_row)

    def run(self, model, dataset: pd.DataFrame, debug_row=False) -> dict:
        """
        Computes the average position of the entry in the validation set
        """
        print(
            "Starting offline evaluation using validation set and recently trained model"
        )

        inference = Inference(model=model, logger=setup_generic_stdout_logger())

        no_performed_tests = 0
        avg_position = 0
        number_of_existing_keys = len(self._configuration.commands.keys())

        dataset = dataset[dataset["label"] == 5]
        print(
            f"Size of dataset after filtering for positive labels: {len(dataset.index)}"
        )
        for index, row in dataset.iterrows():

            if not self.all_keys_exist(row):
                print(f"Members of entry do not existing any longer skipping row")
                continue

            print("Entry row: ")
            pprint.pprint(row.to_dict())

            key = row["key"]
            previous_key = row.get("previous_key")
            previous_previous_key = row.get("previous_previous_key")

            no_performed_tests += 1
            if no_performed_tests == OfflineEvaluation._NUMBER_OF_TESTS:
                break

            input = {
                "hour": row.get("hour"),
                "month": row.get("month"),
                "previous_key": previous_key,
                "previous_previous_key": previous_previous_key,
            }
            print("Model input: ", input)
            input = ModelInput(**input)
            result = inference.get_ranking(predefined_input=input)

            metadata = {
                "position_target": result.index(key),
                "target_key": key,
                "number_of_items_in_ranking": len(result),
                "top_result_preview": result[0:3],
                "bottom_result_preview": result[-3:],
            }
            print("Single result: ")
            pprint.pprint(metadata)
            avg_position += metadata["position_target"]

            if debug_row:
                breakpoint()

        avg_position = avg_position / no_performed_tests
        result = {
            "avg_position_for_positive_class": avg_position,
            "avg_position_for_tests": avg_position,
            "number_of_tests": OfflineEvaluation._NUMBER_OF_TESTS,
            "number_of_existing_keys": number_of_existing_keys,
            "dataset_size": len(dataset.index),
        }
        print("Final Result: ", result)

        return result

    def all_keys_exist(self, row) -> bool:
        if (
            not row.get("key")
            or not row.get("previous_key")
            or not row.get("previous_previous_key")
            or not self._key_exists(row["key"])
            or not self._key_exists(row["previous_key"])
            or not self._key_exists(row["previous_previous_key"])
        ):
            return False
        return True

    def get_X_test_split_of_dataset(self, dataset: DataFrame, X_test) -> pd.DataFrame:
        """
        Returns the X_test split of the dataset
        """
        ids = [int(x) for x in X_test[:, 0].tolist()]
        df = dataset.toPandas()
        test_df = df[df["entry_number"].isin(ids)]
        print("TestDF shape: ", test_df.shape)

        return test_df

    def _key_exists(self, key):
        return key in self._configuration.commands.keys()


def main():
    import fire

    fire.Fire(OfflineEvaluation)


if __name__ == "__main__":
    main()
