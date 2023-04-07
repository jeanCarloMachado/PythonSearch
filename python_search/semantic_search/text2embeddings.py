#!/usr/bin/env python3

import time
from functools import wraps

def timeit(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        end_time = time.time()
        print(f"{method.__name__} => {(end_time-start_time)*1000} ms")

        return result

    return wrapper
class Text2Embeddings():
    @timeit
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

        return embeddings.numpy()


if __name__ == '__main__':
    import fire

    fire.Fire()
