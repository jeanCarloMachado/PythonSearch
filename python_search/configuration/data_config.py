import os

from python_search.configuration.loader import ConfigurationLoader


class DataConfig:
    """
    Configuration with locations of _entries, models and names of files.
    """

    def __init__(self):
        project_root = ConfigurationLoader().get_entries_project_root()
        self.MLFLOW_MODELS_PATH = f"{project_root}/mlflow"

    # output of the _model
    BASE_DATA_FOLDER = f"{os.environ['HOME']}/.python_search/data"
    BASE_DATA_COLLECTOR_FOLDER = f"{os.environ['HOME']}/.python_search/data"
    prediction_batch_location = BASE_DATA_FOLDER + "/predict_input_lenght/latest"
    # a copy of the search run _entries for the feature store
    entries_dump = BASE_DATA_FOLDER + "/entries_dumped/latest"
    entries_dump_file = BASE_DATA_FOLDER + "/entries_dumped/latest/000.parquet"
    cached_configuration = "/tmp/search_and_run_configuration_cached"
    # this path exists in the docker container but not necessarily in the host
    BASELINE_EXPERIMENT_NAME = f"baseline_rank_v0"
    NEXT_ITEM_EXPERIMENT_NAME = f"next_item_v1"
    ENTRY_TYPE_CLASSIFIER_EXPERIMENT_NAME = f"entry_type_classifier_v2"
    OLD_SEARCH_RUNS_PERFORMED_FOLDER = (
        BASE_DATA_FOLDER + "/data_warehouse/dataframes/SearchRunPerformed"
    )
