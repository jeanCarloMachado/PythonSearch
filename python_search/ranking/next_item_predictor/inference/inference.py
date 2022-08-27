from __future__ import annotations

import os
import traceback
from typing import Any, List, Optional

from python_search.config import ConfigurationLoader, PythonSearchConfiguration
from python_search.infrastructure.performance import timeit
from python_search.ranking.models import PythonSearchMLFlow
from python_search.ranking.next_item_predictor.inference.input import \
    InferenceInput
from python_search.ranking.next_item_predictor.transform import Transform


class Inference:
    """
    Performs the ranking inference on all existing keys in the moment
    """

    PRODUCTION_RUN_ID = "7f84f955ebfe429faec18efbd68a7842"

    def __init__(
        self,
        configuration: Optional[PythonSearchConfiguration] = None,
        run_id: Optional[str] = None,
        model: Optional[Any] = None,
    ):

        self.debug = os.getenv("DEBUG", False)
        self.run_id = run_id if run_id else self.PRODUCTION_RUN_ID

        if model:
            print("Using custom passed model")
        else:
            print("Using run id: " + self.run_id)
        configuration = (
            configuration if configuration else ConfigurationLoader().load_config()
        )
        # previous key should be setted in runtime
        self.previous_key = None
        self.all_keys = configuration.commands.keys()
        self._transform = Transform()

        self.model = model if model else self._load_mlflow_model(run_id=self.run_id)

    @timeit
    def get_ranking(
        self, predefined_input: Optional[InferenceInput] = None, return_weights=False
    ) -> List[str]:
        """
        Gets the ranking from the next item model
        """
        print("Number of existing keys: ", str(len(self.all_keys)))
        inference_input = (
            predefined_input
            if predefined_input
            else InferenceInput.with_keys(
                self._transform.inference_embeddings.get_recent_key_with_embedding(),
                self._transform.inference_embeddings.get_recent_key_with_embedding(
                    second_recent=True
                ),
            )
        )

        try:
            X = self._transform.transform_inference(inference_input)
            Y = self._predict(X)
            result = list(zip(self.all_keys, Y))
            result.sort(key=lambda x: x[1], reverse=True)
            if return_weights:
                return result

            only_keys = [entry[0] for entry in result]
            print("Ranking inference succeeded")
        except Exception as e:
            print(
                "Error while performing inference, returning baseline ranking. Details: "
                + e.__str__()
            )

            print(traceback.format_exc())
            only_keys = self.all_keys

        return only_keys

    @timeit
    def _predict(self, X):
        return self.model.predict(X)

    @timeit
    def _load_mlflow_model(self, run_id=None):
        model = PythonSearchMLFlow().get_next_predictor_model(run_id=run_id)
        return model
