import pandas as pd
import wbdata
from pandas_datareader import data as web
import requests
import datetime
import logging
import os
from tenacity import retry, stop_after_attempt, wait_exponential

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api_fetcher')

START_YEAR = 2018
END_YEAR = 2026

# We will collect tidy data here
# Format: [date, frequency, variable_code, variable_name, unit, component_category, value, data_source]
tidy_data_rows = []

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_world_bank():
    logger.info("Fetching World Bank data...")
    # Map component to (Category, Unit)
    indicators = {
        'NE.CON.PRVT.CN': ('Consumption', 'Current LCU'),
        'NE.CON.PRVT.KN': ('Consumption', 'Constant LCU'),
        'NE.CON.GOVT.CN': ('Government Spending', 'Current LCU'),
        'NE.CON.GOVT.KN': ('Government Spending', 'Constant LCU'),
        'NE.GDI.TOTL.CN': ('Investment', 'Current LCU'),
        'NE.GDI.TOTL.KN': ('Investment', 'Constant LCU'),
        'NE.EXP.GNFS.CN': ('Exports', 'Current LCU'),
        'NE.EXP.GNFS.KN': ('Exports', 'Constant LCU'),
        'NE.IMP.GNFS.CN': ('Imports', 'Current LCU'),
        'NE.IMP.GNFS.KN': ('Imports', 'Constant LCU'),
        'NY.GDP.MKTP.CN': ('GDP', 'Current LCU'),
        'NY.GDP.MKTP.KN': ('GDP', 'Constant LCU')
    }
    
    # In wbdata v1.1+, get_dataframe signature: get_dataframe(indicators, country, ...)
    df = wbdata.get_dataframe({k: k for k in indicators.keys()}, country='VNM')
    
    # Filter by date
    df = df.reset_index()
    # If the index was multi-index (country, date)
    if 'country' in df.columns:
        df = df.drop(columns=['country'])
    
    # Process dataframe
    for _, row in df.iterrows():
        year_str = str(row['date'])
        try:
            year_int = int(year_str)
        except:
            year_int = pd.to_datetime(year_str).year

        if START_YEAR <= year_int <= END_YEAR:
            # Add each indicator
            for ind_code, (cat, unit) in indicators.items():
                val = row.get(ind_code)
                if pd.notna(val):
                    tidy_data_rows.append({
                        'date': f"{year_int}-01-01",
                        'frequency': 'Annual',
                        'variable_code': ind_code,
                        'variable_name': f"Vietnam {cat} ({unit})",
                        'unit': unit,
                        'component_category': cat,
                        'value': val,
                        'data_source': 'World Bank (wbdata)'
                    })
    logger.info("World Bank data fetched successfully.")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_fred():
    logger.info("Fetching FRED data...")
    # Try fetching Vietnam Gross Domestic Product, CPI, etc.
    # FRED series: 
    # VNMNGDP: GDP in LCU
    # VNMCPALTT01IXOBQ: CPI
    # VNMNGDPNC: National Accounts: GDP by Expenditure
    indicators = {
        'VNMNGDP': ('GDP', 'Current LCU'),
        'VNMNGCNO': ('Consumption', 'Current LCU'), # Speculative, might not exist
        'VNMNGFI': ('Investment', 'Current LCU'),   # Speculative
        'VNMNGEXP': ('Exports', 'Current LCU'),     # Speculative
        'VNMNGIMP': ('Imports', 'Current LCU')      # Speculative
    }
    
    start_date = datetime.datetime(START_YEAR, 1, 1)
    end_date = datetime.datetime(END_YEAR, 12, 31)
    
    for ind_code, (cat, unit) in indicators.items():
        try:
            df = web.DataReader(ind_code, 'fred', start_date, end_date)
            for date_idx, row in df.iterrows():
                val = row[ind_code]
                if pd.notna(val):
                    tidy_data_rows.append({
                        'date': date_idx.strftime('%Y-%m-%d'),
                        'frequency': 'Annual' if 'A' in ind_code else 'Variable',
                        'variable_code': ind_code,
                        'variable_name': f"Vietnam {cat} ({unit})",
                        'unit': unit,
                        'component_category': cat,
                        'value': val,
                        'data_source': 'FRED (pandas_datareader)'
                    })
            logger.info(f"FRED series {ind_code} fetched successfully.")
        except Exception as e:
            logger.warning(f"Could not fetch FRED series {ind_code}: {e}")
            pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_imf():
    logger.info("Fetching IMF WEO/IFS data...")
    
    # We will try to use dbnomics if installed, else fallback to IMF SDMX API
    try:
        from dbnomics import fetch_series
        # IMF IFS series for Vietnam
        # Annual: A.VN.NGDP_XDC (GDP), A.VN.NCP_XDC (Private Cons), A.VN.NCG_XDC (Gov Cons)
        series_map = {
            'IMF/IFS/A.VN.NGDP_XDC': ('GDP', 'Current LCU'),
            'IMF/IFS/A.VN.NCP_XDC': ('Consumption', 'Current LCU'),
            'IMF/IFS/A.VN.NCG_XDC': ('Government Spending', 'Current LCU'),
            'IMF/IFS/A.VN.NFI_XDC': ('Investment', 'Current LCU'),
            'IMF/IFS/A.VN.NX_XDC': ('Exports', 'Current LCU'),
            'IMF/IFS/A.VN.NM_XDC': ('Imports', 'Current LCU')
        }
        
        for s_code, (cat, unit) in series_map.items():
            try:
                df = fetch_series(s_code)
                if not df.empty:
                    for _, row in df.iterrows():
                        year = int(row.get('period', '0')[:4])
                        if START_YEAR <= year <= END_YEAR:
                            val = row.get('value')
                            if pd.notna(val):
                                tidy_data_rows.append({
                                    'date': f"{year}-01-01",
                                    'frequency': 'Annual',
                                    'variable_code': s_code,
                                    'variable_name': f"Vietnam {cat} ({unit})",
                                    'unit': unit,
                                    'component_category': cat,
                                    'value': val,
                                    'data_source': 'IMF IFS (dbnomics)'
                                })
            except Exception as e:
                logger.warning(f"Failed to fetch IMF series {s_code} via dbnomics: {e}")
    except ImportError:
        logger.warning("dbnomics not available, skipping IMF fetch.")
    except Exception as e:
        logger.warning(f"IMF fetch encountered an error: {e}")

def main():
    logger.info("Starting API fetcher for Vietnam Macro Data...")
    
    try:
        fetch_world_bank()
    except Exception as e:
        logger.error(f"World Bank fetch failed: {e}")
        
    try:
        fetch_fred()
    except Exception as e:
        logger.error(f"FRED fetch failed: {e}")
        
    try:
        fetch_imf()
    except Exception as e:
        logger.error(f"IMF fetch failed: {e}")
        
    if len(tidy_data_rows) == 0:
        logger.error("No data fetched from any sources!")
        return
        
    df_tidy = pd.DataFrame(tidy_data_rows)
    # Reorder columns just to be safe
    cols = ['date', 'frequency', 'variable_code', 'variable_name', 'unit', 'component_category', 'value', 'data_source']
    df_tidy = df_tidy[cols]
    
    # Save to CSV
    output_path = '/Users/justindinh/.gemini/antigravity/scratch/vietnam_macro_data/api_data.csv'
    df_tidy.to_csv(output_path, index=False)
    logger.info(f"Successfully saved tidy data to {output_path} ({len(df_tidy)} rows)")

if __name__ == "__main__":
    main()
