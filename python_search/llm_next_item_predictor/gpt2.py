

def inference():
    from transformers import pipeline, set_seed
    generator = pipeline('text-generation', model='gpt2')
    set_seed(42)
    result = generator("germans are ", max_length=30, num_return_sequences=5)
    return result

if __name__ == "__main__":
    import fire
    fire.Fire()