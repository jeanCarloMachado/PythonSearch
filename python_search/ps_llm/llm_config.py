import os

HOME = os.environ["HOME"]
BASE_PROJECT_FOLDER = HOME + "/.python_search"


class LLMConfig:
    """
    Configuration for your Large Language Model, customizable in entries_main.py
    """

    def __init__(self):
        from python_search.configuration.loader import ConfigurationLoader

        config = ConfigurationLoader().load_config()
        custom_llm_config = None
        if config.custom_llm_config is not None:
            custom_llm_config = config.custom_llm_config

        self.TARGET_VERSION = "v15"
        self.NEW_MODEL_RELATIVE_TARGET_DIRECTORY = (
            "t5_llm_models/model_" + self.TARGET_VERSION
        )
        self.BASE_MODEL_PATH = BASE_PROJECT_FOLDER + "/t5_llm_models"
        self.FULL_MODEL_PATH = (
            BASE_PROJECT_FOLDER + "/" + self.NEW_MODEL_RELATIVE_TARGET_DIRECTORY
        )
        self.NEXT_ITEM_PRODUCTIONALIZED_MODEL = (
            self.BASE_MODEL_PATH + "/model_v12_epoch_3"
            if not custom_llm_config
            else custom_llm_config.next_item_productionalized_model
        )
        self.SUMMARIZATION_PRODUCTIONALIZED_MODEL = (
            self.NEXT_ITEM_PRODUCTIONALIZED_MODEL
        )
        self.BASE_MODEL_TO_TRAIN_OVER = "t5-base"
        self.BASE_DATASET_FOLDER = BASE_PROJECT_FOLDER + "/datasets"
        self.BASE_ORIGINAL_MODEL = (
            "t5-small"
            if not custom_llm_config
            else custom_llm_config.base_original_model
        )


class CustomLLMConfig:
    """
    Customize the Path and name of your Custom LLM Model in your entries_main.py
    """

    def __init__(
        self,
        base_original_model: str,
        next_item_productionalized_model: str,
    ):
        self.base_original_model = base_original_model
        self.next_item_productionalized_model = next_item_productionalized_model
