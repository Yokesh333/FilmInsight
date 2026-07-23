import os
import glob

cache_dir = r"C:\Users\Yokesh\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\1110a243fdf4706b3f48f1d95db1a4f5529b4d41"

for file in glob.glob(os.path.join(cache_dir, "*")):
    if os.path.isfile(file):
        size = os.path.getsize(file)
        print(f"{os.path.basename(file)}: {size} bytes")
