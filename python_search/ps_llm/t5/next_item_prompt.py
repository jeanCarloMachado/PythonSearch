class PromptBuilder:
    """
    Builds the prompt for train or inference
    """

    PROMPT_START = "Predict the next key given this history: "

    def build_prompt_inference(self, history):
        prompt = f"{self.PROMPT_START} "

        for i in range(0, len(history)):
            prompt += f" {i+1}. {history[i]}"
            if i > 5:
                break

        return prompt

    def build_prompt_for_spark(self, row):
        prompt = f"{self.PROMPT_START} "

        if row["previous_1"] is not None:
            prompt += f" 1. {row['previous_1']}"
        if row["previous_2"] is not None:
            prompt += f" 2. {row['previous_2']}"
        if row["previous_3"] is not None:
            prompt += f" 3. {row['previous_3']}"
        if row["previous_4"] is not None:
            prompt += f" 4. {row['previous_4']}"
        if row["previous_5"] is not None:
            prompt += f" 5. {row['previous_5']}"

        return prompt
