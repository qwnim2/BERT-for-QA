import json
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import *
from tqdm.auto import trange, tqdm
import os
from pathlib import Path

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

output_dir = ('../model_save_測試/')
model = BertForQuestionAnswering.from_pretrained(output_dir)
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese', do_lower_case=True)

model.to(device)
batch_size = 4

class EarlyDataset(Dataset):
  def __init__(self, path: str, tokenizer: BertTokenizer) -> None:
    self.tokenizer = tokenizer
    self.data = []
    with open(path) as f:
      for article in json.load(f)['data']:
        parapraphs = article['paragraphs']
        for para in parapraphs:
          context = para['context']
          for qa in para['qas']:
            qa_id = qa['id']
            question = qa['question']
            self.data.append((qa_id, context, question))

  def __len__(self):
    return len(self.data)

  def __getitem__(self, index: int):
    qa_id, context, question = self.data[index]
    return qa_id, context, question

test_dataset = EarlyDataset("../dev.json", tokenizer)
test_loader = DataLoader(test_dataset, batch_size=batch_size)

best_valid_loss = float('inf')
all_predictions = {}

model.eval()
with torch.no_grad():
  pbar=tqdm(test_loader)
  for batch in pbar:
    ids, contexts, questions = batch
    eval_input = []
    for i in range(batch_size):
        context = ()
        question_len = len(questions[i])
        context_max_len = 509 - question_len
        if len(contexts[i])>context_max_len:      #truncate
          context=contexts[i][:context_max_len]
        else:
          context=contexts[i]
        eval_input.append([context, questions[i]])
    #print(eval_input)
    input_dict = tokenizer.batch_encode_plus(eval_input,
                                              max_length=tokenizer.max_len, 
                                              pad_to_max_length=True,
                                              return_tensors='pt')
    input_dict = {k: v.to(device) for k, v in input_dict.items()}
    print(input_dict)
    start ,end = model(**input_dict, start_positions=None, end_positions=None)
    #print(f"start: {start}")
    #print(f"end: {end}")
    #for i in range(batch_size):
      
      #print(f"start_scores: {start_scores}")
      #print(f"end_scores: {start_scores}")
      # probs = logits.softmax(-1)[:, 1]
      # print(probs)
      # all_predictions.update(
      #     {
      #         uid: 'answer' if prob > 0.66 else ''

      #         for uid, prob in zip(ids, probs)
      #     }
      #   )

#Path("./predict.json").write_text(json.dumps(all_predictions))