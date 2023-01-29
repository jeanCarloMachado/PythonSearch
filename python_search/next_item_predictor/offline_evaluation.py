import pandas as pd
from pyspark.sql import DataFrame

from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.configuration.loader import ConfigurationLoader
from python_search.next_item_predictor.inference.inference import Inference
from python_search.next_item_predictor.inference.input import ModelInput


class OfflineEvaluation:
    """
    Evaluate the model with the validation set
    """

    _NUMBER_OF_TESTS = 100

    def __init__(self):
        self._configuration: PythonSearchConfiguration = ConfigurationLoader().load_config()

    def run_current_model(self):
        model_class = self._configuration.get_next_item_predictor_model()
        model = model_class.load_mlflow_model()

        dataset = model_class.load_or_build_dataset()

        self.run(model, dataset.toPandas())


    def run(self, model, dataset: pd.DataFrame) -> dict:
        """
        Computes the average position of the entry in the validation set
        """
        print(
            "Starting offline evaluation using validation set and recently trained model"
        )

        inference = Inference(model=model)

        total_found = 0
        avg_position = 0
        number_of_existing_keys = len(self._configuration.commands.keys())
        for index, row in dataset.iterrows():
            key = row["key"]
            previous_key = row.get("previous_key")
            previous_previous_key = row.get("previous_previous_key")

            if (
                not key
                or not previous_key
                or not previous_previous_key
                or not self._key_exists(row["key"])
                or not self._key_exists(row["previous_key"])
                or not self._key_exists(row["previous_previous_key"])
            ):
                print(
                    f"Members of entry do not existing any longer ({key}, {previous_key}, {previous_previous_key})"
                )
                continue

            total_found += 1
            if total_found == OfflineEvaluation._NUMBER_OF_TESTS:
                break

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
            print("Metadata: ", metadata)
            avg_position += metadata["position_target"]

        avg_position = avg_position / total_found
        result = {
            "avg_position_for_tests": avg_position,
            "number_of_tests": OfflineEvaluation._NUMBER_OF_TESTS,
            "number_of_existing_keys": number_of_existing_keys,
            "dataset_size": dataset.count(),
        }
        print("Result: ", result)

        return result

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

if __name__ == '__main__':
    main()
