def get_spark():
    from pyspark.sql.session import SparkSession

    return (
        SparkSession.builder.config("spark.executor.memory", "15g")
        .config("spark.driver.memory", "10g")
        .config("spark.memory.offHeap.enabled", True)
        .config("spark.memory.offHeap.size", "16g")
        .getOrCreate()
    )
