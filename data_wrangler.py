import pandas as pd
import numpy as np
import os

def process_data():
    # Use absolute paths for reliability
    base_dir = '/Users/justindinh/.gemini/antigravity/scratch/vietnam_macro_data/'
    api_path = os.path.join(base_dir, 'api_data.csv')
    local_path = os.path.join(base_dir, 'local_data.csv')
    
    try:
        df_api = pd.read_csv(api_path)
    except Exception as e:
        print(f"Error reading api_data: {e}")
        df_api = pd.DataFrame()
        
    try:
        df_local = pd.read_csv(local_path)
    except Exception as e:
        print(f"Error reading local_data: {e}")
        df_local = pd.DataFrame()
        
    df = pd.concat([df_api, df_local], ignore_index=True)
    
    expected_cols = ['date', 'frequency', 'variable_code', 'variable_name', 'unit', 'component_category', 'value', 'data_source']
    
    for col in expected_cols:
        if col not in df.columns:
            if col == 'value':
                df[col] = np.nan
            else:
                df[col] = 'Unknown'
                
    df = df[expected_cols]
    
    # Handle dates: Convert to datetime, coerce errors to NaT
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Handle values: string replacements if needed, then to numeric
    if df['value'].dtype == 'O':
        df['value'] = df['value'].astype(str).str.replace(',', '', regex=False)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    # Handle missing values according to context
    df['value'] = df['value'].fillna(0.0)
    
    # Fill remaining text columns missing with 'Unknown'
    text_cols = ['frequency', 'variable_code', 'variable_name', 'unit', 'component_category', 'data_source']
    df[text_cols] = df[text_cols].fillna('Unknown')
    
    out_parquet = os.path.join(base_dir, 'vietnam_macro_demand_2018_2026.parquet')
    out_csv = os.path.join(base_dir, 'vietnam_macro_demand_2018_2026.csv')
    
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False)
    
    print(f"Total records processed: {len(df)}")
    print("Files successfully generated:")
    print(f"  - {out_parquet}")
    print(f"  - {out_csv}")

if __name__ == '__main__':
    process_data()
