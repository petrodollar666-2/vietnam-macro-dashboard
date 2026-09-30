import pandas as pd
import numpy as np
from datetime import datetime
import os

def generate_mock_data():
    dates = pd.date_range(start='2018-01-01', end='2026-09-01', freq='MS')
    
    variables = [
        {'code': 'RETAIL', 'name': 'Tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tiêu dùng', 'unit': 'Tỷ VNĐ', 'category': 'Domestic Demand'},
        {'code': 'CPI', 'name': 'Chỉ số giá tiêu dùng (CPI)', 'unit': 'Index', 'category': 'Inflation'},
        {'code': 'INV', 'name': 'Vốn đầu tư thực hiện từ nguồn ngân sách Nhà nước', 'unit': 'Tỷ VNĐ', 'category': 'Investment'},
        {'code': 'EXP', 'name': 'Kim ngạch xuất khẩu', 'unit': 'Triệu USD', 'category': 'Trade'},
        {'code': 'IMP', 'name': 'Kim ngạch nhập khẩu', 'unit': 'Triệu USD', 'category': 'Trade'}
    ]
    
    data = []
    
    np.random.seed(42)
    
    for date in dates:
        for var in variables:
            # Generate some realistic looking trend data with seasonality and noise
            time_factor = (date.year - 2018) * 12 + date.month
            
            if var['code'] == 'RETAIL':
                base_val = 300000 + time_factor * 2000
                seasonality = 50000 if date.month in [1, 2] else 0 # Tet holiday spike
                value = base_val + seasonality + np.random.normal(0, 10000)
            elif var['code'] == 'CPI':
                value = 100 + time_factor * 0.3 + np.random.normal(0, 0.5)
            elif var['code'] == 'INV':
                base_val = 20000 + time_factor * 500
                seasonality = base_val * 0.5 if date.month == 12 else 0 # Year end disbursement
                value = base_val + seasonality + np.random.normal(0, 2000)
            elif var['code'] == 'EXP':
                base_val = 20000 + time_factor * 200
                value = base_val + np.random.normal(0, 1500)
            elif var['code'] == 'IMP':
                base_val = 19500 + time_factor * 190
                value = base_val + np.random.normal(0, 1500)
                
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'frequency': 'M',
                'variable_code': var['code'],
                'variable_name': var['name'],
                'unit': var['unit'],
                'component_category': var['category'],
                'value': round(value, 2),
                'data_source': 'GSO/Customs (Mock Data)'
            })
            
    df = pd.DataFrame(data)
    
    output_path = '/Users/justindinh/.gemini/antigravity/scratch/vietnam_macro_data/local_data.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {len(df)} rows of data and saved to {output_path}")

if __name__ == "__main__":
    generate_mock_data()
