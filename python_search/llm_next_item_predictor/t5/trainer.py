from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.utils.data import Dataset, DataLoader
import torch

from python_search.llm_next_item_predictor.next_item_llm_dataset import LLMDataset
from python_search.llm_next_item_predictor.t5.config import T5ModelConfig

# Define the dataset class
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
        input_tokenized = self.tokenizer.encode_plus(input, max_length=self.max_length, padding='max_length',
                                                     truncation=True, return_tensors='pt')
        target_tokenized = self.tokenizer.encode_plus(target, max_length=self.max_length, padding='max_length',
                                                      truncation=True, return_tensors='pt')
        return {
            'input_ids': input_tokenized['input_ids'].flatten(),
            'attention_mask': input_tokenized['attention_mask'].flatten(),
            'labels': target_tokenized['input_ids'].flatten()
        }


class T5Train:

    def __init__(self):
        self.tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
        print("Device to train on:", self.device)
        self.MODEL_DIRECTORY = T5ModelConfig.MODEL_DIRECTORY

    def train(self, epochs=1):
        # Initialize the tokenizer and model
        print(f"Training for {epochs} epochs")
        model = T5ForConditionalGeneration.from_pretrained('t5-small')

        df = LLMDataset().load()


        # Let's assume you have a DataFrame `df` with 'input_text' and 'target_text' columns
        inputs = df['prompt'].tolist()
        targets = df['label'].tolist()

        # Prepare the DataLoader
        dataset = T5Dataset(inputs, targets, self.tokenizer, max_length=512)
        dataloader = DataLoader(dataset, batch_size=16)

        # Define the device
        print("Device:", self.device)
        model.to(self.device)

        # Define optimizer
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        # Training loop
        model.train()
        for epoch in range(0, epochs):  # number of epochs
            print(f"Epoch {epoch + 1}")
            for batch in dataloader:
                optimizer.zero_grad()
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                # forward pass
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)

                # compute the loss
                loss = outputs.loss
                loss.backward()

                # update parameters
                optimizer.step()

            print(f"Epoch {epoch + 1} Loss: {loss.item()}")

        model.save_pretrained(self.MODEL_DIRECTORY)


def main():
    import fire
    fire.Fire()

if __name__ == "__main__":
    main()
