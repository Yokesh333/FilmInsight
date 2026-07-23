import os
import sys

from transformers import AutoTokenizer

model_id = "sentence-transformers/all-MiniLM-L6-v2"
print(f"Trying to load tokenizer for {model_id}")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
