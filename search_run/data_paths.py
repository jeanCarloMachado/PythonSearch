class DataPaths:
    # output of the model
    prediction_batch_location = "/data/python_search/predict_input_lenght/latest"
    # a copy of the search run entries for the feature store
    entries_dump = "/data/python_search/entries_dumped/latest"
    entries_dump_file = "/data/python_search/entries_dumped/latest/000.parquet"
    commands_performed = "/data/grimoire/message_topics/run_key_command_performed"
    cached_configuration = "/tmp/search_and_run_configuration_cached"
