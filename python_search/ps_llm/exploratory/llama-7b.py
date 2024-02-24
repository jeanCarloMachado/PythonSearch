from transformers import LlamaTokenizer, AutoModelForCausalLM

tokenizer = LlamaTokenizer.from_pretrained("decapoda-research/llama-7b-hf")
model = AutoModelForCausalLM.from_pretrained("decapoda-research/llama-7b-hf")
model.to("mps")


text = "test jean"
input_ids = tokenizer(text, return_tensors="pt").input_ids.to("mps")
print("Starting inference")
generated_ids = model.generate(input_ids, max_length=10)
print(tokenizer.decode(generated_ids[0], skip_special_tokens=True))
