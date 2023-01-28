from pyspark.sql import DataFrame

from python_search.configuration.loader import ConfigurationLoader
from python_search.next_item_predictor.inference.inference import Inference
from python_search.next_item_predictor.inference.input import ModelInput


class OfflineEvaluation:
    """
    Evaluate the model with the validation set
    """

    NUMBER_OF_TESTS = 150

    def run(self, model, dataset: DataFrame, X_test) -> dict:
        """
        Computes the average position of the entry in the validation set
        """
        self._configuration = ConfigurationLoader().load_config()
        print(
            "Starting offline evaluation using validation set and recently trained model"
        )
        ids = [int(x) for x in X_test[:, 0].tolist()]
        df = dataset.toPandas()
        test_df = df[df["entry_number"].isin(ids)]
        print("TestDF shape: ", test_df.shape)

        inference = Inference(model=model)

        total_found = 0
        avg_position = 0
        number_of_existing_keys = len(self._configuration.commands.keys())
        for index, row in test_df.iterrows():

            key = row["key"]
            previous_key = row.get("previous_key")
            previous_previous_key = row.get("previous_previous_key")

            if (
                not self._key_exists(row["key"])
                or ("previous_key" in row and not self._key_exists(row["previous_key"]))
                or (
                    "previous_previous_key" in row
                    and not self._key_exists(row["previous_previous_key"])
                )
            ):
                print(
                    f"Members of entry do not existing any longer ({key}, {previous_key}, {previous_previous_key})"
                )
                continue

            input = ModelInput(
                hour=row.get("hour"),
                month=row.get("month"),
                previous_key=previous_key,
                previous_previous_key=previous_previous_key,
            )
            result = inference.get_ranking(predefined_input=input)

            metadata = {
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
