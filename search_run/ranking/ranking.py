import json
from collections import namedtuple

import pandas as pd
import pyspark.sql.functions as F
from grimoire.decorators import notify_execution
from grimoire.file import write_file
from grimoire.search_run.entries.main import Configuration

from search_run.logger import configure_logger
from search_run.ranking.ciclical import CiclicalPlacement

logger = configure_logger()


class Ranking:
    """
    Write to the file all the commands and generates shortcuts
    """

    ModelInfo = namedtuple("ModelInfo", "features label")
    model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self):
        self.configuration = Configuration
        self.cached_file = Configuration.cached_filename

    @notify_execution()
    def recompute_rank(self):
        """
        Recomputes the rank and saves the results on the file to be read
        """

        entries: dict = self.load_entries()
        commands_performed = self.load_commands_performed_df()

        result = CiclicalPlacement().cyclical_placment(entries, commands_performed)

        return self._export_to_file(result)

    def load_commands_performed_df(self):
        """
        Returns a pandas datafarme with the commands performed
        """
        with open("/data/grimoire/message_topics/run_key_command_performed") as f:
            data = []
            for line in f.readlines():
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    logger.debug(f"Line broken: {line}")
        df = pd.DataFrame(data)

        # revert the list (latest on top)
        df = df.iloc[::-1]

        return df

    def load_commands_performed_dataframe(self, spark):
        dataset = Ranking().load_commands_performed_df()
        schema = "`key` STRING,  `generated_date` STRING, `uuid` STRING, `given_input` STRING"
        original_df = spark.createDataFrame(dataset, schema=schema)
        performed_df = original_df.withColumn("input_lenght", F.length("given_input"))
        performed_df = performed_df.filter('given_input != "NaN"')
        performed_df = performed_df.drop("uuid")

        return performed_df

    def _export_to_file(self, data):
        fzf_lines = ""
        for name, content in data:

            try:
                content["key_name"] = name
                content = json.dumps(content, default=tuple, ensure_ascii=True)
            except:
                content = content
                content = str(content)

            fzf_lines += f"{name.lower()}: " +  content + "\n"

        fzf_lines = fzf_lines.replace('\\', '\\\\')
        write_file(self.configuration.cached_filename, fzf_lines)

    def load_entries_df(self, spark):
        """
        loads a spark dataframe with the configuration entries
        """
        entries = self.load_entries()

        entries
        entries = [
            {"key": entry[0], "content": f"{entry[1]}", "position": position + 1}
            for position, entry in enumerate(entries.items())
        ]
        # entries

        rdd = spark.sparkContext.parallelize(entries)

        entries_df = spark.read.json(rdd)
        entries_df = entries_df.drop("_corrupt_record")
        entries_df = entries_df.withColumn("key_lenght", F.length("key"))

        return entries_df

    def load_entries(self):
        return self.configuration().commands
