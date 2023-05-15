


class LLMDataset():

    PROMPT_START = "Which key will user use next given this recent history: "

    def generate(self, limit=1000):
        from python_search.events.run_performed.dataset import EntryExecutedDataset

        data = EntryExecutedDataset().load_new()
        df = data.sort("timestamp", ascending=False)
        print(f"Limiting to {limit} entries...")
        df = df.limit(limit)

        from pyspark.sql.functions import lag, concat_ws, lit, concat
        from pyspark.sql.window import Window
        windowSpec = Window.orderBy("timestamp")  # assuming "index" is the column that orders your data


        df = df.withColumn("previous_1", lag(df['key']).over(windowSpec))
        df = df.withColumn("previous_2", lag(df['key'], 2).over(windowSpec))
        df = df.withColumn("previous_3", lag(df['key'], 3).over(windowSpec))

        df = df.withColumnRenamed("key", "label")
        df = df.withColumn("prompt", concat(lit(self.PROMPT_START),
                                            concat_ws(",", "previous_1", "previous_2", "previous_3")))

        df = df.select("prompt", "label")

        df.show()
        df = df.toPandas()

        import os
        home = os.path.expanduser("~")
        destination = home+"/.python_search/dataset.pkl"
        print("Saving to:", destination)
        df.to_pickle(destination)
        print("dataset size in the folder: ")
        import subprocess;
        subprocess.check_output("du -sh "+destination, shell=True, text=True)

    def load(self):
        import os
        home = os.path.expanduser("~")
        import pandas as pd
        df = pd.read_pickle(home+"/.python_search/dataset.pkl")
        return df

    def inspect(self):
        return self.load().to_string()

if __name__ == "__main__":
    import fire
    fire.Fire()

