from transformers import T5ForConditionalGeneration, AutoTokenizer
import torch

model = T5ForConditionalGeneration.from_pretrained(
    "google/flan-ul2", device_map="auto", load_in_8bit=True
)
tokenizer = AutoTokenizer.from_pretrained("google/flan-ul2")

input_string = "Answer the following question by reasoning step by step. The cafeteria had 23 apples. If they used 20 for lunch, and bought 6 more, how many apple do they have?"

inputs = tokenizer(input_string, return_tensors="pt").input_ids.to("cuda")
outputs = model.generate(inputs, max_length=200)

print(tokenizer.decode(outputs[0]))
