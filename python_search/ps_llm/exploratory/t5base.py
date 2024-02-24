from transformers import T5ForConditionalGeneration, T5Tokenizer

model_name = "t5-base"

model = T5ForConditionalGeneration.from_pretrained(model_name)
model.to("mps")
tokenizer = T5Tokenizer.from_pretrained(model_name)

input_string = "test jean"

inputs = tokenizer(input_string, return_tensors="pt").input_ids.to("mps")
outputs = model.generate(inputs, max_length=200)


print("Result:")
print(tokenizer.decode(outputs[0]))
