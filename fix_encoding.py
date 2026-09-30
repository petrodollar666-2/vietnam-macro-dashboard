import pandas as pd
import ftfy
import os

file_path = "raw_data.csv"
parquet_path = "vietnam_macro_static_dump.parquet"

def fix_encoding(text):
    if pd.isna(text):
        return text
    if not isinstance(text, str):
        text = str(text)
    # Attempt to fix mojibake using ftfy
    return ftfy.fix_text(text)

print(f"Reading {file_path}...")
try:
    # Try reading with utf-8 first
    df = pd.read_csv(file_path, encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv(file_path, encoding='latin1')
    except Exception as e:
        print(f"Failed to read file: {e}")
        exit(1)

print("Applying encoding fixes to text columns...")
text_columns = ['variable_name', 'component_category', 'data_source']

for col in text_columns:
    if col in df.columns:
        df[col] = df[col].apply(fix_encoding)

print("Unique values in 'variable_name' after fix:")
if 'variable_name' in df.columns:
    for val in df['variable_name'].unique():
        print(f"  - {val}")
else:
    print("  'variable_name' column not found.")

print(f"Saving to {file_path} with encoding='utf-8-sig'...")
df.to_csv(file_path, index=False, encoding='utf-8-sig')

print(f"Saving to {parquet_path}...")
df.to_parquet(parquet_path, engine='pyarrow', index=False)

print("Done.")
