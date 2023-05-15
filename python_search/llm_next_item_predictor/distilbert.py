from python_search.llm_next_item_predictor.dataset import LLMDataset


class Distilbert():

    def train(self, epochs=1):
        import torch
        from transformers import EncoderDecoderModel, DistilBertTokenizer

        # Load DistilBERT model
        model = EncoderDecoderModel.from_encoder_decoder_pretrained('distilbert-base-uncased', 'bert-base-uncased')

        # Load a tokenizer
        tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

        df = LLMDataset().load()

        # Let's assume you have a DataFrame `df` with 'input_text' and 'target_text' columns
        input_text = df['prompt'].tolist()
        target_text = df['label'].tolist()

        # Tokenize input and target text
        input_tokenized = tokenizer(input_text, padding=True, truncation=True, return_tensors="pt")
        target_tokenized = tokenizer(target_text, padding=True, truncation=True, return_tensors="pt")

        # Specify the device
        device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        print("Device:", device)
        model.to(device)
        batch_size = 16

        from transformers import AdamW

        # Specify the learning rate
        learning_rate = 1e-5

        # Initialize the optimizer
        optimizer = AdamW(model.parameters(), lr=learning_rate)

        # Define the training loop
        model.train()
        for epoch in range(epochs):
            for i in range(len(input_text)):
                #input_ids = input_tokenized['input_ids'][i].to(device)
                #target_ids = target_tokenized['input_ids'][i].to(device)
                input_ids = input_tokenized['input_ids'][i].unsqueeze(0).to(device)
                target_ids = target_tokenized['input_ids'][i].unsqueeze(0).to(device)

                outputs = model(input_ids=input_ids, decoder_input_ids=target_ids)
                loss = outputs.loss
                loss.backward()

                if i % batch_size == 0:
                    optimizer.step()
                    optimizer.zero_grad()
        print("Train finished")
        breakpoint()



if __name__ == "__main__":
    import fire
    fire.Fire()
[]