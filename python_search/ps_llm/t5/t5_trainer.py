from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.utils.data import Dataset, DataLoader
import torch
from tqdm import tqdm

from python_search.ps_llm.llm_dataset import LLMDataset
from python_search.ps_llm.llm_config import LLMConfig

from python_search.ps_llm.utils import timer, Timer


def get_device(use_xla=False, force_cuda=False) -> str:
    if torch.backends.mps.is_available():
        print("Foudn apple metal device")
        return "mps"

    if use_xla:
        print("Assuming XLA device")
        import torch_xla.core.xla_model as xm

        return xm.xla_device()

    if torch.cuda.is_available() or force_cuda:
        print("Cuda device enabled")
        return "cuda"

    return "cpu"


# Define the dataset class
class T5Train:
    def __init__(self):
        self.TARGET_MODEL_DIRECTORY = LLMConfig.FULL_MODEL_PATH
        print("Model directory to save on:", self.TARGET_MODEL_DIRECTORY)

    @timer
    def train(
        self,
        *,
        epochs=10,
        base_model_path=None,
        use_xla=False,
        force_cuda=False,
        batch_size=8,
    ):
        self.device = get_device(use_xla, force_cuda)
        print("Device to train on:", self.device)

        # Initialize the tokenizer and model
        print(f"Training for {epochs} epochs")

        if not base_model_path:
            base_model_path = LLMConfig.BASE_MODEL_TO_TRAIN_OVER
        print("Using Base model path:", base_model_path)

        self.tokenizer = T5Tokenizer.from_pretrained(LLMConfig.BASE_ORIGINAL_MODEL)
        model = T5ForConditionalGeneration.from_pretrained(base_model_path)

        df = LLMDataset().load()

        # Let's assume you have a DataFrame `df` with 'input_text' and 'target_text' columns
        inputs = df["prompt"].tolist()
        targets = df["label"].tolist()

        # Prepare the DataLoader
        dataset = T5Dataset(inputs, targets, self.tokenizer, max_length=512)
        print("Batch size is:", batch_size)
        dataloader = DataLoader(dataset, batch_size=batch_size)

        # Define the device
        print("Device:", self.device)
        model.to(self.device)

        # Define optimizer
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        # Training loop
        model.train()
        for epoch in range(0, epochs):  # number of epochs
            print(f"Epoch {epoch + 1}")
            timer = Timer()
            for batch in tqdm(dataloader):
                optimizer.zero_grad()
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                # forward pass
                outputs = model(
                    input_ids=input_ids, attention_mask=attention_mask, labels=labels
                )

                # compute the loss
                loss = outputs.loss
                loss.backward()

                # update parameters
                optimizer.step()

            epoch_folder = self.TARGET_MODEL_DIRECTORY + "_epoch_" + str(epoch + 1)
            print(
                f"Epoch finished {epoch + 1} Loss: {loss.item()} Saving model to: {epoch_folder}"
            )
            model.save_pretrained(epoch_folder)
            timer.report("Finished epoch")


class T5Dataset(Dataset):
    def __init__(self, inputs, targets, tokenizer, max_length):
        self.inputs = inputs
        self.targets = targets
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        input = self.inputs[idx]
        target = self.targets[idx]
        input_tokenized = self.tokenizer.encode_plus(
            input,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        target_tokenized = self.tokenizer.encode_plus(
            target,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": input_tokenized["input_ids"].flatten(),
            "attention_mask": input_tokenized["attention_mask"].flatten(),
            "labels": target_tokenized["input_ids"].flatten(),
        }


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
