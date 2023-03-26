#!/usr/bin/env python3

class Embeddings():
    def transform(self, text: str):
        import torch
        from transformers import DistilBertModel, DistilBertTokenizer
        # Load the pre-trained DistilBERT tokenizer
        tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

        model = DistilBertModel.from_pretrained('distilbert-base-uncased')
        tokens = tokenizer.encode_plus(text, add_special_tokens=True, return_tensors='pt')

        # Obtain embeddings
        with torch.no_grad():
            outputs = model(**tokens)
            embeddings = outputs[0][:, 0, :]

        print(embeddings)
        print(type(embeddings))

        return embeddings.numpy()


if __name__ == '__main__':
    import fire

    fire.Fire()
