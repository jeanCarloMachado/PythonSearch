from typing import List

from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.utils.data import Dataset, DataLoader
import torch

from python_search.llm_next_item_predictor.llmdataset import LLMDataset
from python_search.search.entries_loader import EntriesLoader


# Define the dataset class
class MyDataset(Dataset):
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


class T5ModelConfig:
    MODEL_DIRECTORY = 'my_model_directory'


class T5Model:

    def __init__(self):
        self.tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.config = T5ModelConfig()

    def load_trained_model(self):
        # Load the model
        print("Loading model from:", self.config.MODEL_DIRECTORY)
        model = T5ForConditionalGeneration.from_pretrained(self.config.MODEL_DIRECTORY)

        # Ensure the model is in evaluation mode
        model.eval()
        return model, self.tokenizer


class T5Train:

    def __init__(self):

        self.tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.MODEL_DIRECTORY = T5ModelConfig.MODEL_DIRECTORY

    def train(self, epochs=1):
        # Initialize the tokenizer and model
        model = T5ForConditionalGeneration.from_pretrained('t5-small')

        df = LLMDataset().load()

        # Let's assume you have a DataFrame `df` with 'input_text' and 'target_text' columns
        inputs = df['prompt'].tolist()
        targets = df['label'].tolist()

        # Prepare the DataLoader
        dataset = MyDataset(inputs, targets, self.tokenizer, max_length=512)
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

        model.save_pretrained(self.modle_directory)



class RankInference:

    def __init__(self):
        self.model, self.tokenizer = T5Model().load_trained_model()

    def rank(self):

        history = ['gmail', 'gmail', 'gmail']

        prompt = LLMDataset.PROMPT_START + ",".join(history)
        print("Prompt:", prompt)
        inference_result = self.inference(",".join(history))
        #inference_result = 'news'

        entries_keys = EntriesLoader().load_all_keys()[0:100]
        embeddings = self.get_embeddings_efficient([inference_result])
        embeddings_entries = [ self.get_embeddings_efficient(entry)[0] for entry in entries_keys]

        result = []
        for i, entry in enumerate(entries_keys):
            similarity = torch.nn.functional.cosine_similarity(embeddings_entries[i], embeddings[0], dim=0)
            result.append((entry, similarity.item()))
            #print("Similarity:", similarity.item())

        result.sort(key=lambda x: x[1], reverse=True)
        return result

    def inference(self, recent_history):
        # Load the model
        # Now you can use the model for prediction
        with torch.no_grad():
            inputs = LLMDataset.PROMPT_START + recent_history
            print("Input:", inputs)

            inputs_tokenized = self.tokenizer.encode_plus(inputs, return_tensors='pt')
            input_ids = inputs_tokenized['input_ids'].to('cpu')
            attention_mask = inputs_tokenized['attention_mask'].to('cpu')

            # Generate prediction
            outputs = self.model.generate(input_ids=input_ids, attention_mask=attention_mask)

            # Decode the prediction
            predicted_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print('Output: ', predicted_text)
        return predicted_text


    def get_embeddings_efficient(self, sentences: List[str]):
        import torch

        # Tokenize all sentences and convert to tensor format
        inputs = self.tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

        with torch.no_grad():
            # Generate the outputs from the model
            outputs = self.model.encoder(inputs['input_ids']).last_hidden_state

        # Average the embeddings to get sentence-level embeddings
        sentence_embeddings = torch.mean(outputs, dim=1)

        return sentence_embeddings

    def similarity(self, sentence1, sentence2):
        from torch.nn.functional import cosine_similarity
        # Compute cosine similarity
        embeddings = self.get_embeddings_efficient([sentence1, sentence2])
        similarity = cosine_similarity(embeddings[0], embeddings[1], dim=0)
        print("Cosine similarity:", similarity.item())

def main():
    import fire
    fire.Fire()

if __name__ == "__main__":
    main()

