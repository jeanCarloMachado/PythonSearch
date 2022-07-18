from python_search.ranking.next_item_predictor.inference import (
    Inference, InferenceInput)


class OfflineEvaluation:
    def run(self, model, dataset, X_test):
        """
        Computes the average position of the entray in the validation set
        """
        print("Starting offline evaluation!")
        ids = [int(x) for x in X_test[:, 0].tolist()]
        df = dataset.toPandas()
        test_df = df[df["entry_number"].isin(ids)]
        print("TestDF shape: ", test_df.shape)

        from python_search.ranking.next_item_predictor.inference import (
            Inference, InferenceInput)

        inference = Inference(model=model)

        def key_exists(key):
            return key in inference.configuration.commands.keys()

        total_found = 0
        number_of_tests = 20
        avg_position = 0
        number_of_existing_keys = len(inference.configuration.commands.keys())
        for index, row in test_df.iterrows():
            if not key_exists(row["previous_key"]) or not key_exists(row["key"]):
                print(
                    f"Key pair does not exist any longer ({row['previous_key']}, {row['key']})"
                )
                continue

            input = InferenceInput(
                hour=row["hour"], month=row["month"], previous_key=row["previous_key"]
            )
            result = inference.get_ranking(predefined_input=input, return_weights=False)

            metadata = {
                "pair": row["previous_key"] + " -> " + row["key"],
                "position_target": result.index(row["key"]),
                "Len": len(result),
                "type of result": type(result),
            }
            print(metadata)

            avg_position += metadata["position_target"]
            total_found += 1
            if total_found == number_of_tests:
                break

        avg_position = avg_position / number_of_tests
        result = {
            "avg_position_for_tests": avg_position,
            "number_of_tests": number_of_tests,
            "number_of_existing_keys": number_of_existing_keys,
        }
        print(result)

        return result
