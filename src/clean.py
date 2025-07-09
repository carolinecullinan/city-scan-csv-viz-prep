#!/usr/bin/env python3
"""
tabular output csv cleanup script

Takes csv files from existing City Scan tabular output and interim Scan Calculation Sheet data outputs and cleans up formatting and makes additional calculations so that the output is ready for visualization, returning new csv files:

"""

import pandas as pd
import sys

def clean_pg(input_file, output_file=None):
    """
    clean up the population-growth.csv file for visualization as pg.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file
    output_file : str, optional
        Path for output.
    """
    
    # read the population growth CSV file
    df = pd.read_csv(input_file)
    
    # sort by year to ensure correct order
    df = df.sort_values('Year').reset_index(drop=True)
    
    # create new dataframe with desired structure
    result_df = pd.DataFrame({
        'yearName': df['Year'],
        'population': df['Population']
    })
    
    # calculate population growth percentage
    # growth percentage = ((current_year - previous_year) / previous_year) * 100
    result_df['populationGrowthPercentage'] = result_df['population'].pct_change() * 100
    
    # round to 3 decimal places to match your example
    result_df['populationGrowthPercentage'] = result_df['populationGrowthPercentage'].round(3)
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/pg.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Years covered: {result_df['yearName'].min()} - {result_df['yearName'].max()}")
    print(f"Total data points: {len(result_df)}")
    print(f"Population range: {result_df['population'].min():,} - {result_df['population'].max():,}")
    
    return result_df

# command line usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean.py input_file.csv [output_file.csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    clean_pg(input_file, output_file)