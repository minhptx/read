from read.seed.verification.module import Seed3Module
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
from accelerate import Accelerator
from datasets import Dataset
from tango import Step, Format, JsonFormat
from typing import Optional


@Step.register("seed_table_verification")
class SeedTableVerification(Step):
    DETERMINISTIC: bool = True
    CACHEABLE: Optional[bool] = True
    FORMAT: Format = JsonFormat()
    VERSION: Optional[str] = "002"


    def run(self, model, tokenizer, data, sentence_results):
        verified_results = []
        for i, (example, result) in enumerate(zip(data, sentence_results)):
            verified_result = []
            for sent in result:
                if self.verify(sent, example["table"]):
                    verified_result.append(True)
                    break
            else:
                verified_result.append(False)
        return verified_results


    def veriy(self, model, tokenizer, linearized_tables, sentences):
        inputs = tokenizer(linearized_tables, sentences, truncation=True, padding=True, return_tensors="pt")
        inputs = {k: v.cuda() for k, v in inputs.items()}

        dataset = Dataset.from_dict(inputs)

        dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])
        dataloader = DataLoader(dataset, batch_size=8, num_workers=4)

        accelerator = Accelerator()

        self.model, self.tokenizer, dataloader = accelerator.prepare(self.model, self.tokenizer, dataloader)

        all_preds = []

        for batch in dataloader:
            batch = {k: v.cuda() for k, v in batch.items()}
            preds = model(**batch).logits.argmax(dim=1)

            all_preds.extend(preds.tolist())

        return all_preds
