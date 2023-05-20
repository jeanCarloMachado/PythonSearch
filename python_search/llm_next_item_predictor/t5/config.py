import os

HOME = os.environ["HOME"]


class T5ModelConfig:
    """
    Configuration for the T5 model
    """

    VERSION = "v2"
    NEW_MODEL_TARGET_DIRECTORY = "t5_llm_models/" + VERSION
    BASE_MODEL_PATH = HOME + "/.python_search/t5_llm_models"
    FULL_MODEL_PATH = BASE_MODEL_PATH + NEW_MODEL_TARGET_DIRECTORY
    PRODUCTIONALIZED_MODEL = BASE_MODEL_PATH + "/production_model"


