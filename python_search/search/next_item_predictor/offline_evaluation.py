from pyspark.sql import DataFrame

from python_search.config import ConfigurationLoader
from python_search.search.next_item_predictor.inference.inference import Inference
from python_search.search.next_item_predictor.inference.input import ModelInput


class OfflineEvaluation:
    """
    Evaluate the _model with a part of the training _entries
    """

    NUMBER_OF_TESTS = 100

    def run(self, model, dataset: DataFrame, X_test):
        """
        Computes the average position of the entry in the validation set
        """
        self._configuration = ConfigurationLoader().load_config()
        print("Starting offline evaluation")
        ids = [int(x) for x in X_test[:, 0].tolist()]
        df = dataset.toPandas()
        test_df = df[df["entry_number"].isin(ids)]
        print("TestDF shape: ", test_df.shape)

        inference = Inference(model=model)

        total_found = 0
        avg_position = 0
        number_of_existing_keys = len(self._configuration.commands.keys())
        for index, row in test_df.iterrows():

            if (
                not self._key_exists(row["key"])
                or not self._key_exists(row["previous_key"])
                or not self._key_exists(row["previous_previous_key"])
            ):
                print(
                    f"Key pair does not exist any longer ({row['previous_key']}, {row['key']})"
                )
                continue

            input = ModelInput(
                hour=row["hour"],
                month=row["month"],
                previous_key=row["previous_key"],
                previous_previous_key=row["previous_previous_key"],
            )
            result = inference.get_ranking(predefined_input=input)

            metadata = {
                "pair": row["previous_key"] + " -> " + row["key"],
                "position_target": result.index(row["key"]),
                "Len": len(result),
                "type of result": type(result),
            }
            print(metadata)

            avg_position += metadata["position_target"]
            total_found += 1
            if total_found == OfflineEvaluation.NUMBER_OF_TESTS:
                break

        avg_position = avg_position / OfflineEvaluation.NUMBER_OF_TESTS
        result = {
            "avg_position_for_tests": avg_position,
            "number_of_tests": OfflineEvaluation.NUMBER_OF_TESTS,
            "number_of_existing_keys": number_of_existing_keys,
            "dataset_size": dataset.count(),
        }
        print(result)

        return result

    def _key_exists(self, key):
        return key in self._configuration.commands.keys()
