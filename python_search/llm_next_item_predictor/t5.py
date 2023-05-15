from transformers import T5Tokenizer, T5ForConditionalGeneration
from torch.utils.data import Dataset, DataLoader
import torch

from python_search.llm_next_item_predictor.llmdataset import LLMDataset


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



class T5Train:

    def __init__(self):

        self.tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.MODEL_DIRECTORY = 'my_model_directory'

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

    def load_model(self):
        # Load the model
        print("Loading model from:", self.MODEL_DIRECTORY)
        model = T5ForConditionalGeneration.from_pretrained(self.MODEL_DIRECTORY)

        # Ensure the model is in evaluation mode
        model.eval()
        return model, self.tokenizer


    def inference(self, recent_history):
        # Load the model

        model, tokenizer = self.load_model()
        # Now you can use the model for prediction
        with torch.no_grad():
            inputs = LLMDataset.PROMPT_START + recent_history
            print("Input:", inputs)
            #inputs = "translate English to French: The cat sat on the mat."

            inputs_tokenized = tokenizer.encode_plus(inputs, return_tensors='pt')
            input_ids = inputs_tokenized['input_ids'].to('cpu')
            attention_mask = inputs_tokenized['attention_mask'].to('cpu')

            # Generate prediction
            outputs = model.generate(input_ids=input_ids, attention_mask=attention_mask)

            # Decode the prediction
            predicted_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print('Output: ', predicted_text)

class Rank:
    def get_embeddings(self):
        import torch
        from transformers import T5Tokenizer, T5Model

        # Load the fine-tuned T5 model and the tokenizer

        model, tokenizer = T5Train().load_model()

        # Two example sentences
        sentence1 = "king"
        sentence2 = "queen"

        # Tokenize the sentences and convert to tensor format
        input1 = tokenizer(sentence1, return_tensors='pt')
        input2 = tokenizer(sentence2, return_tensors='pt')


        with torch.no_grad():
            output1 = model.encoder(input1['input_ids']).last_hidden_state
            output2 = model.encoder(input2['input_ids']).last_hidden_state

        # Average the embeddings to get sentence-level embeddings
        sentence_embedding1 = torch.mean(output1, dim=1)
        sentence_embedding2 = torch.mean(output2, dim=1)

        print(sentence_embedding1)
        print(sentence_embedding2)
        from torch.nn.functional import cosine_similarity

        # Compute cosine similarity
        similarity = cosine_similarity(sentence_embedding1, sentence_embedding2)
        print("Cosine similarity:", similarity.item())



if __name__ == "__main__":
    import fire

    fire.Fire()

