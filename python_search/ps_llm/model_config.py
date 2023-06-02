import os

HOME = os.environ["HOME"]

class ModelConfig:
    """
    Configuration for the T5 model
    """

    TARGET_VERSION = "v13"
    NEW_MODEL_RELATIVE_TARGET_DIRECTORY = "t5_llm_models/model_" + TARGET_VERSION
    BASE_MODEL_PATH = HOME + "/.python_search/t5_llm_models"
    FULL_MODEL_PATH = HOME + "/.python_search/" + NEW_MODEL_RELATIVE_TARGET_DIRECTORY
    SUMMARIZATION_PRODUCTIONALIZED_MODEL = BASE_MODEL_PATH + '/model_v12_epoch_3'
    NEXT_ITEM_PRODUCTIONALIZED_MODEL = SUMMARIZATION_PRODUCTIONALIZED_MODEL
    BASE_MODEL_TO_TRAIN_OVER = 't5-base'
    BASE_ORIGINAL_MODEL = 't5-base'
