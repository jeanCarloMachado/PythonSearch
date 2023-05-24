import os

HOME = os.environ["HOME"]


class T5ModelConfig:
    """
    Configuration for the T5 model
    """

    TARGET_VERSION = "v6"
    NEW_MODEL_RELATIVE_TARGET_DIRECTORY = "t5_llm_models/model_" + TARGET_VERSION
    BASE_MODEL_PATH = HOME + "/.python_search/t5_llm_models"
    FULL_MODEL_PATH = HOME + "/.python_search/" + NEW_MODEL_RELATIVE_TARGET_DIRECTORY
    PRODUCTIONALIZED_MODEL = BASE_MODEL_PATH + "/model_v4_epoch_4"
    BASE_MODEL_TO_TRAIN_OVER = BASE_MODEL_PATH + '/v2_epoch_16'



