import os

HOME = os.environ["HOME"]
BASE_PROJECT_FOLDER = HOME + "/.python_search"
if 'CUSTOM_BASE_FOLDER' in os.environ:
    print("Using custom base folder: ", os.environ['CUSTOM_BASE_FOLDER'])
    BASE_PROJECT_FOLDER = os.environ['CUSTOM_BASE_FOLDER']

class LLMConfig:
    """
    Configuration for the T5 model
    """

    TARGET_VERSION = "v15"
    NEW_MODEL_RELATIVE_TARGET_DIRECTORY = "t5_llm_models/model_" + TARGET_VERSION
    BASE_MODEL_PATH = BASE_PROJECT_FOLDER + "/t5_llm_models"
    FULL_MODEL_PATH = BASE_PROJECT_FOLDER+ "/" + NEW_MODEL_RELATIVE_TARGET_DIRECTORY
    NEXT_ITEM_PRODUCTIONALIZED_MODEL = '/Users/jean.machado/Library/CloudStorage/GoogleDrive-jean.machado@getyourguide.com/My Drive/PythonSearchDataInDrive/t5_llm_models/model_v14_epoch_9'
    SUMMARIZATION_PRODUCTIONALIZED_MODEL = NEXT_ITEM_PRODUCTIONALIZED_MODEL
    BASE_MODEL_TO_TRAIN_OVER = 't5-base'
    BASE_DATASET_FOLDER = BASE_PROJECT_FOLDER + "/datasets"
    BASE_ORIGINAL_MODEL = 't5-base'
