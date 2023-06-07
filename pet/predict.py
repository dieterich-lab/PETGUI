import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import glob

df = pd.read_csv("./data_uploaded/unlabeled/unlabeled.csv", header=None, names=['label', 'text'])
tokenizer = BertTokenizer.from_pretrained('output/final/p0-i0')
model = BertForSequenceClassification.from_pretrained('./output/final/p0-i0')
input_ids = []
attention_masks = []
for text in df['text']:
    encoded_dict = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=64,
        pad_to_max_length=True,
        return_attention_mask=True,
        return_tensors='pt'
    )
    input_ids.append(encoded_dict['input_ids'])
    attention_masks.append(encoded_dict['attention_mask'])
input_ids = torch.cat(input_ids, dim=0)
attention_masks = torch.cat(attention_masks, dim=0)
labels = torch.tensor(df['label'].values)
with torch.no_grad():
    outputs = model(input_ids, attention_mask=attention_masks)
logits = outputs[0]
predictions = torch.argmax(logits, dim=1)
df['label'] = predictions
df.to_csv('predictions.csv', index=False)
