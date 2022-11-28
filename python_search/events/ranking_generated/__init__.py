from __future__ import annotations
from typing import  List, Union
import uuid

from pydantic import BaseModel

EVENT_FOLDER = "ranking_generated"


NotSetYet = None

class RankingGenerated(BaseModel):
    # name of the entry matched
    ranking: List[str]
    # unix timestamp
    first: Union[str, NotSetYet] = NotSetYet
    uuid: Union[str, NotSetYet] = NotSetYet
    timestamp: Union[str, NotSetYet] = NotSetYet

class RankingGeneratedWriter:
    def write(self, event: RankingGenerated):
        import datetime

        event.timestamp = str(datetime.datetime.now(datetime.timezone.utc).timestamp())
        event.uuid = str(uuid.uuid4())
        event.first = event.ranking[0]

        return GenericDataCollector().write(
            data=event.__dict__, table_name=EVENT_FOLDER
        )



from python_search.config import DataConfig
from python_search.data_collector import GenericDataCollector


class RankingGeneratedDataset:
    """
    Poit of acess for the searches performed
    This is the place to keep the source of truth for the schema as well
    """

    DATA_FOLDER = DataConfig.BASE_DATA_COLLECTOR_FOLDER + "/" + EVENT_FOLDER

    def __init__(self, spark=None):
        from pyspark.sql.session import SparkSession
        self.spark = spark if spark else SparkSession.builder.getOrCreate()

    def load(self):
        return self.spark.read.json(self.DATA_FOLDER)
