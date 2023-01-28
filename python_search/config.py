"""
Clients should depend on a configuration instance (config) rather than in the class,
the class should only be used for type annotation.
This way we can have multiple configs depending of the environment.
"""
import os

from python_search.environment import is_mac


class DataConfig:
    """
    Configuration with locations of _entries, models and names of files.
    """

    # output of the _model
    base_data_folder = f"{os.environ['HOME']}/.data/data/python_search"
    BASE_DATA_COLLECTOR_FOLDER = f"{os.environ['HOME']}/.data/data_collection"
    prediction_batch_location = base_data_folder + "/predict_input_lenght/latest"
    # a copy of the search run _entries for the feature store
    entries_dump = base_data_folder + "/entries_dumped/latest"
    entries_dump_file = base_data_folder + "/entries_dumped/latest/000.parquet"
    cached_configuration = "/tmp/search_and_run_configuration_cached"
    # this path exists in the docker container but not necessarily in the host
    MLFLOW_MODELS_PATH = f"/entries/mlflow"
    BASELINE_EXPERIMENT_NAME = f"baseline_rank_v0"
    NEXT_ITEM_EXPERIMENT_NAME = f"next_item_v1"
    ENTRY_TYPE_CLASSIFIER_EXPERIMENT_NAME = f"entry_type_classifier_v2"
    DATA_WAREHOUSE_FOLDER = base_data_folder + "/data_warehouse"
    CLEAN_EVENTS_FOLDER = DATA_WAREHOUSE_FOLDER + "/clean"
    SEARCH_RUNS_PERFORMED_FOLDER = (
        base_data_folder + "/data_warehouse/dataframes/SearchRunPerformed"
    )


class MLFlowConfig:
    port = 5002


class KafkaConfig:
    default_port: str = "9092"
    host: str = f"127.0.0.1:{default_port}"


class RedisConfig:
    host = "127.0.0.1" if is_mac() else "host.docker.internal"
    port = 6379
