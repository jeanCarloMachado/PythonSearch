from python_search.ps_llm.llm_dataset import LLMDataset
from python_search.ps_llm.t5.t5_model import T5Model
from tqdm import tqdm


class Evaluate:
    """
    Evaluate performance of the model on a validation set giving a global score and one per task
    """

    def all_for_model(self, model_path=None) -> None:
        classify_type = self.from_pretrained_classify_type(model_path)
        print("Classify type: ", classify_type)

        title_generator = self.from_pretrained_title_generator(model_path)
        print("Title generator: ", title_generator)

        next_item = self.from_pretrained_next_item(model_path)
        print("Next item: ", next_item)

        global_score = self.from_pretrained(model_path)
        print("Global score: ", global_score)

        return {
            "global_score": global_score,
            "next_item": next_item,
            "classify_type": classify_type,
            "title_generator": title_generator,
        }

    def from_pretrained_classify_type(self, model_path=None) -> float:
        from python_search.ps_llm.tasks.classity_entry_type import ClassifyEntryType

        return self.from_pretrained(
            model_path=model_path, starts_with=ClassifyEntryType.PROMPT_START
        )

    def from_pretrained_next_item(self, model_path=None) -> float:
        from python_search.ps_llm.t5.next_item_prompt import PromptBuilder

        return self.from_pretrained(
            model_path=model_path, starts_with=PromptBuilder.PROMPT_START
        )

    def from_pretrained_title_generator(self, model_path=None) -> float:
        from python_search.ps_llm.tasks.entry_title_generator import EntryTitleGenerator

        return self.from_pretrained(
            model_path=model_path, starts_with=EntryTitleGenerator.PROMPT_START
        )

    def from_pretrained(self, model_path=None, starts_with=None) -> float:
        """
        Performs the evaluation of a model given its path and the latest dataset
        """
        data = LLMDataset().load_validation()
        if starts_with:
            print("Starts with set, so will filter by it")
            data = data[data["prompt"].str.startswith(starts_with)]
            print("Lenght after filtering by starts_with: " + str(len(data)))
        else:
            print("No starts with set, so will use all data")

        model = T5Model.load_trained_model(model_path)
        return self.perform(model, data)

    def perform(self, model, data):
        similarity = Similarity()
        print("Performing inference in all validation rows")
        data["predicted"] = [
            model.predict(row["prompt"]) for index, row in tqdm(data.iterrows())
        ]
        print("Compute similarity between predicted and label")
        data["similarity"] = [
            similarity.compute(row["predicted"], row["label"])
            for index, row in tqdm(data.iterrows())
        ]

        similarity_mean = data["similarity"].mean()

        print("Sample of rows")
        print(data.iloc[[0]])
        print(data.iloc[[1]])
        print(data.iloc[[-1]])

        return similarity_mean


class Similarity:
    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer("distilbert-base-nli-mean-tokens")

    def compute(self, sentence1, sentence2):
        from sentence_transformers import util

        sentence_embeddings = self.model.encode([sentence1, sentence2])
        result = util.pytorch_cos_sim(sentence_embeddings[0], sentence_embeddings[1])
        return float(result[0][0])


if __name__ == "__main__":
    import fire

    fire.Fire()
