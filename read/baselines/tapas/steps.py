import torch
import json
from tango import Step
from tango.common.dataset_dict import DatasetDict
import pandas as pd
from transformers import TapasTokenizer

class TableDataset(torch.utils.data.Dataset):
    def __init__(self, df, tokenizer):
        self.df = df
        self.tokenizer = tokenizer

    def __getitem__(self, idx):
        ex_id = idx % 2
        idx = idx // 2
        item = self.df.iloc[idx]
        table = pd.DataFrame(json.loads(item["table"]))
        cells = zip(*item["highlighted_cells"])
        cells = [list(x) for x in cells]
        sub_table = table.iloc[cells[0], cells[1]].reset_index().astype(str)

        if ex_id == 0:
            encoding = self.tokenizer(
                table=sub_table,
                queries=item["positive"],
                padding="max_length",
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoding["label"] = torch.tensor([1])
        else:
            encoding = self.tokenizer(
                table=sub_table,
                queries=item["negative"],
                padding="max_length",
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoding["label"] = torch.tensor([0])

        encoding = {key: val[-1] for key, val in encoding.items()}
        return encoding

    def __len__(self):
        return len(self.df)


@Step.register("tapas_input_data")
class GenerateData(Step):
    DETERMINISTIC = True
    CACHEABLE = False

    def run(self, tokenizer, train_file, dev_file) -> DatasetDict:
        tokenizer = TapasTokenizer.from_pretrained(tokenizer)
        torch.manual_seed(1)
        train_df = pd.read_json(train_file, lines=True)
        dev_df = pd.read_json(dev_file, lines=True)

        train_dataset = TableDataset(train_df, tokenizer)
        dev_dataset = TableDataset(dev_df, tokenizer)
        return DatasetDict(
            {
                "train": train_dataset,
                "validation": dev_dataset,
            }
        )