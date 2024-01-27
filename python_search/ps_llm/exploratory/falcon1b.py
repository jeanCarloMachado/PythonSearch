from transformers import AutoTokenizer, AutoModelForCausalLM
import transformers
import torch

model = "tiiuae/falcon-rw-1b"

tokenizer = AutoTokenizer.from_pretrained(model)

model = AutoModelForCausalLM.from_pretrained(model, trust_remote_code=True)
model.to("mps")
inputs = tokenizer("test jean", return_tensors="pt").to("mps").input_ids
outputs = model.generate(inputs, max_length=200)

print(tokenizer.decode(outputs[0]))
