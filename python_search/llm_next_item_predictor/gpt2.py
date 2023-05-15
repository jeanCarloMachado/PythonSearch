

class GPT2Trainer:

    def load_dataset(self):
        from transformers import GPT2Tokenizer, TextDataset

        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

        def load_dataset(train_path, test_path, tokenizer):
            train_dataset = TextDataset(
                tokenizer=tokenizer,
                file_path=train_path,
                block_size=128)

            test_dataset = TextDataset(
                tokenizer=tokenizer,
                file_path=test_path,
                block_size=128)

            return train_dataset, test_dataset

        train_dataset, test_dataset = load_dataset('train.txt', 'test.txt', tokenizer)


    def train(self):
        from transformers import Trainer, TrainingArguments, GPT2LMHeadModel

        model = GPT2LMHeadModel.from_pretrained('gpt2')

        training_args = TrainingArguments(
            output_dir="./gpt2_finetuned",  # The output directory
            overwrite_output_dir=True,  # overwrite the content of the output directory
            num_train_epochs=3,  # number of training epochs
            per_device_train_batch_size=32,  # batch size for training
            per_device_eval_batch_size=64,  # batch size for evaluation
            eval_steps=400,  # Number of update steps between two evaluations.
            save_steps=800,  # after # steps model is saved
            warmup_steps=500,  # number of warmup steps for learning rate scheduler
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            data_collator=lambda data: {'input_ids': torch.stack([f[0] for f in data]),
                                        'attention_mask': torch.stack([f[1] for f in data]),
                                        'labels': torch.stack([f[0] for f in data])},
            train_dataset=train_dataset,
            eval_dataset=test_dataset
        )

        trainer.train()
        trainer.save_model()


def inference():
    from transformers import pipeline, set_seed
    generator = pipeline('text-generation', model='gpt2')
    set_seed(42)
    result = generator("germans are ", max_length=30, num_return_sequences=5)
    return result

if __name__ == "__main__":
    import fire
    fire.Fire()