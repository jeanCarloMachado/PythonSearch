from typing import List


def to_embedding(sentences: List[str]):
    import torch
    from transformers import DistilBertModel, DistilBertTokenizer, logging

    logging.set_verbosity_error()
    # Load the pretrained DistilBERT model and tokenizer
    model_name = "distilbert-base-uncased"
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    model = DistilBertModel.from_pretrained(model_name)

    # Your list of strings

    # Tokenize the strings
    input_tokens = tokenizer(
        sentences, return_tensors="pt", padding=True, truncation=True
    )

    # Convert tokenized inputs to PyTorch tensors
    input_ids = input_tokens["input_ids"]
    attention_mask = input_tokens["attention_mask"]

    # Pass the tensors through the model to get embeddings
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)

    # Extract the embeddings from the model output (last hidden states)
    embeddings = outputs.last_hidden_state

    # If you want to get the sentence embeddings by mean-pooling the token embeddings
    return torch.mean(embeddings, dim=1)


def to_embedding2(sentences: List[str]):
    import torch, tqdm
    from transformers import DistilBertModel, DistilBertTokenizer

    batch_size = 32

    # Load the pretrained DistilBERT model and tokenizer
    model_name = "distilbert-base-uncased"
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    model = DistilBertModel.from_pretrained(model_name)

    # Your list of strings

    embeddings = []
    for i in tqdm.tqdm(range(0, len(sentences), batch_size), desc="Processing batches"):
        batch_texts = sentences[i : i + batch_size]
        inputs = tokenizer(
            batch_texts, return_tensors="pt", padding=True, truncation=True
        )
        with torch.no_grad():
            outputs = model(**inputs)
        batch_embeddings = outputs.last_hidden_state
        embedding_list = [i for i in torch.mean(batch_embeddings, dim=1)]

        embeddings = embeddings + embedding_list

    return embeddings
