from typing import Tuple

import numpy as np
from pyspark.sql import DataFrame

class ModelInterface:
    def build_dataset(self) -> DataFrame:
        raise Exception("Not implemented")

    def transform_collection(
            self, dataset: DataFrame
    )->Tuple[np.ndarray, np.ndarray]:
        """
        Returns X and Y
        :param dataset:
        :return:
        """
        raise Exception("Not implemented")

    def transform_single(self, inference_input) -> np.ndarray:
        """
        Return X
        :param inference_input:
        :return:
        """
        raise Exception("Not implemented")
