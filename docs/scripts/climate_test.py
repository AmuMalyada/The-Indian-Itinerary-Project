#!/usr/bin/env python3
"""
Climate Intelligence Integration Script - Simplified Test Version
"""
import pandas as pd
from pathlib import Path

# Get paths
BASE_DIR = Path(__file__).parent.parent
TEMP_CSV = BASE_DIR / 'raw_data' / 'temperatureData.csv'
ATTR_CSV = BASE_DIR / 'final_dataset' / 'attractions_flat_powerbi.csv'
OUTPUT_FILE = BASE_DIR / 'climate_integration_report.txt'

def main():
    with open(OUTPUT_FILE, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("CLIMATE INTELLIGENCE INTEGRATION REPORT\n")
        f.write("=" * 70 + "\n\n")
        
        # Load data
        f.write("[1/5] Loading temperature data...\n")
        temp_df = pd.read_csv(TEMP_CSV)
        f.write(f"✓ Loaded {len(temp_df)} cities from {TEMP_CSV.name}\n")
        f.write(f"  Columns: {list(temp_df.columns[:5])}...\n\n")
        
        f.write("[2/5] Loading attractions data...\n")
        attr_df = pd.read_csv(ATTR_CSV)
        f.write(f"✓ Loaded {len(attr_df)} attractions from {ATTR_CSV.name}\n")
        f.write(f"✓ Unique cities: {attr_df['city_name'].nunique()}\n\n")
        
        # City matching analysis
        f.write("[3/5] Analyzing city matching...\n")
        temp_locs = set(temp_df['location'].str.lower().str.strip())
        attraction_cities = set(attr_df['city_name'].str.lower().str.strip())
        
        matched_cities = attraction_cities & temp_locs
        matched_records = attr_df['city_name'].isin(temp_df['location']).sum()
        
        f.write(f"✓ Unique cities in temperature data: {len(temp_locs)}\n")
        f.write(f"✓ Unique cities in attractions: {len(attraction_cities)}\n")
        f.write(f"✓ Matching cities: {len(matched_cities)}\n")
        f.write(f"✓ Coverage: {100*len(matched_cities)/len(attraction_cities):.1f}%\n")
        f.write(f"✓ Attraction records covered: {matched_records}/{len(attr_df)} ({100*matched_records/len(attr_df):.1f}%)\n\n")
        
        if len(attraction_cities) - len(matched_cities) > 0:
            unmatched = list(attraction_cities - temp_locs)[:5]
            f.write(f"⚠ Unmatched cities (sample): {unmatched}\n\n")
        
        # Map temperature data
        f.write("[4/5] Mapping temperature data to attractions...\n")
        
        # Create temperature dict
        temp_dict = {}
        for _, row in temp_df.iterrows():
            temp_dict[row['location'].lower().strip()] = row
        
        # Add temperature columns to attractions
        temp_cols = [col for col in temp_df.columns if col != 'location']
        
        mapped_count = 0
        for idx, row in attr_df.iterrows():
            city_lower = row['city_name'].lower().strip()
            if city_lower in temp_dict:
                temp_row = temp_dict[city_lower]
                for col in temp_cols:
                    if col not in attr_df.columns:
                        attr_df[col] = None
                    attr_df.at[idx, col] = temp_row[col]
                mapped_count += 1
        
        f.write(f"✓ Mapped {mapped_count} attractions with temperature data\n")
        f.write(f"✓ Success rate: {100*mapped_count/len(attr_df):.1f}%\n\n")
        
        # Calculate derived metrics
        f.write("[5/5] Calculating derived climate metrics...\n")
        
        max_temp_cols = [f'{month}_MaxTemp' for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                                                            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']]
        min_temp_cols = [f'{month}_MinTemp' for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                                                            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']]
        
        attr_df['avg_max_temp_c'] = attr_df[max_temp_cols].mean(axis=1)
        attr_df['avg_min_temp_c'] = attr_df[min_temp_cols].mean(axis=1)
        attr_df['avg_temp_c'] = (attr_df['avg_max_temp_c'] + attr_df['avg_min_temp_c']) / 2
        
        f.write(f"✓ Added average temperature columns\n")
        f.write(f"✓ Temperature range: {attr_df['avg_max_temp_c'].min():.1f}°C to {attr_df['avg_max_temp_c'].max():.1f}°C\n")
        f.write(f"✓ Avg min: {attr_df['avg_min_temp_c'].min():.1f}°C to {attr_df['avg_min_temp_c'].max():.1f}°C\n\n")
        
        # Save enhanced CSV
        output_csv = BASE_DIR / 'final_dataset' / 'attractions_with_climate.csv'
        attr_df.to_csv(output_csv, index=False)
        f.write(f"✓ Saved enhanced CSV to {output_csv.name}\n")
        f.write(f"✓ Records: {len(attr_df)}\n")
        f.write(f"✓ Columns: {len(attr_df.columns)}\n\n")
        
        f.write("=" * 70 + "\n")
        f.write("CLIMATE INTELLIGENCE INTEGRATION SUCCESSFUL\n")
        f.write("=" * 70 + "\n\n")
        f.write("Next steps:\n")
        f.write("1. Update Streamlit app to display climate features\n")
        f.write("2. Add temperature trend charts\n")
        f.write("3. Display best time to visit recommendations\n")
        f.write("4. Show seasonal suitability matrix\n")

if __name__ == '__main__':
    main()
