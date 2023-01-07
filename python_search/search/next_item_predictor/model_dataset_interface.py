import numpy as np
from pyspark.sql import DataFrame

class ModelDatasetInterface:
    def build_dataset(self):
        raise Exception("Not implemented")

    def transform_collection(
            self, dataset: DataFrame
    ):
        raise Exception("Not implemented")

    def transform_single(self, inference_input) -> np.ndarray:
        raise Exception("Not implemented")
