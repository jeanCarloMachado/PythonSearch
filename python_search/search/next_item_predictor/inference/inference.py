from __future__ import annotations

import os
from typing import Any, List, Optional

from python_search.config import ConfigurationLoader, PythonSearchConfiguration
from python_search.infrastructure.performance import timeit
from python_search.logger import setup_inference_logger
from python_search.search.models import PythonSearchMLFlow
from python_search.search.next_item_predictor.inference.input import ModelInput
from python_search.search.next_item_predictor.transform import ModelTransform

logger = setup_inference_logger()


class Inference:
    """
    Performs the search inference on all existing keys in the moment
    """

    PRODUCTION_RUN_ID = "239c1788635344c0acf98b8c8f26fff2"

    def __init__(
        self,
        configuration: Optional[PythonSearchConfiguration] = None,
        run_id: Optional[str] = None,
        model: Optional[Any] = None,
    ):

        self.debug = os.getenv("DEBUG", False)
        self.run_id = run_id if run_id else self.PRODUCTION_RUN_ID
        if "FORCE_RUN_ID" in os.environ:
            self.run_id = os.environ["FORCE_RUN_ID"]

        if model:
            logger.info("Using custom passed _model")
        else:
            logger.info("Using run id: " + self.run_id)
        configuration = (
            configuration if configuration else ConfigurationLoader().load_config()
        )
        # previous key should be setted in runtime
        self.previous_key = None
        self.all_keys = configuration.commands.keys()
        self._transform = ModelTransform()

        try:
            self.model = model if model else self._load_mlflow_model(run_id=self.run_id)
        except Exception as e:
            print("Failed to load mlflow model")
            self.model = None
            raise e

    @timeit
    def get_ranking(self, predefined_input: Optional[ModelInput] = None) -> List[str]:
        """
        Gets the search from the next item _model
        """
        logger.info("Number of existing keys for inference: " + str(len(self.all_keys)))
        inference_input = (
            predefined_input
            if predefined_input
            else ModelInput.with_given_keys(
                self._transform.inference_embeddings.get_recent_key_with_embedding(),
                self._transform.inference_embeddings.get_recent_key_with_embedding(
                    second_recent=True
                ),
            )
        )
        logger.info("Inference input: " + str(inference_input.__dict__))

        X = self._transform.transform_single(inference_input, self.all_keys)
        Y = self._predict(X)
        result = list(zip(self.all_keys, Y))
        result.sort(key=lambda x: x[1], reverse=True)

        only_keys = [entry[0] for entry in result]
        logger.info("Ranking inference succeeded")

        # logger.debug("Only keys: ", only_keys)
        return only_keys

    @timeit
    def _predict(self, X):
        return self.model.predict(X)

    @timeit
    def _load_mlflow_model(self, run_id=None):
        model = PythonSearchMLFlow().get_next_predictor_model(run_id=run_id)
        return model
