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

def clean_pas(input_file, output_file=None):
    """
    clean up the population age structure csv file (i.e., 2025-02-city-country_02-process-output_tabular_city_demographics.csv) for visualization as pas.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file
    output_file : str, optional
        Path for output.
    """
    
    # read the population age structure CSV file
    df = pd.read_csv(input_file)
    
    # combine 0-1 and 1-4 age brackets into 0-4
    df['age_group'] = df['age_group'].replace({'0-1': '0-4', '1-4': '0-4'})
    
    # group by the new age brackets and sex, summing the population
    df_grouped = df.groupby(['age_group', 'sex'], as_index=False)['population'].sum()
    
    # create new dataframe with desired structure, renaming columns appropriately
    result_df = pd.DataFrame({
        'ageBracket': df_grouped['age_group'],
        'sex': df_grouped['sex'].replace({'f': 'female', 'm': 'male'}),  # expand abbreviations
        'count': df_grouped['population'].round(2),  # round to 2 decimal places
        'percentage': (df_grouped['population'] / df_grouped['population'].sum() * 100).round(7),  # calculate percentage
        'yearName': 2021  # assuming 2021 based on most up-to-date data from data source as noted in the Scan Calculation Sheet
    })
    
    # sort by age bracket and sex for consistent ordering
    # get all unique age brackets from the data and create a comprehensive sort order
    unique_brackets = sorted(result_df['ageBracket'].unique())
    
    # create a custom sort order that includes all brackets in the data
    age_order = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', 
                 '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', 
                 '65-69', '70-74', '75-79', '80+', '80']
    
    # add any missing brackets from the data to the end of the order
    for bracket in unique_brackets:
        if bracket not in age_order:
            age_order.append(bracket)
    
    # create a categorical column for proper sorting, only including categories that exist in the data
    existing_categories = [cat for cat in age_order if cat in unique_brackets]
    
    try:
        result_df['age_sort'] = pd.Categorical(result_df['ageBracket'], categories=existing_categories, ordered=True)
        result_df = result_df.sort_values(['age_sort', 'sex']).drop('age_sort').reset_index(drop=True)
        # remove the temporary age_sort column - ensure it's dropped
        if 'age_sort' in result_df.columns:
            result_df = result_df.drop('age_sort', axis=1)
    except Exception as e:
        print(f"⚠️  Warning: Could not sort by age bracket ({e}). Using default sorting.")
        result_df = result_df.sort_values(['ageBracket', 'sex']).reset_index(drop=True)
    
   # final check to ensure age_sort column is not in the output
    if 'age_sort' in result_df.columns:
        result_df = result_df.drop('age_sort', axis=1)
   
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/pas.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Total population: {result_df['count'].sum():,.0f}")
    print(f"Age brackets: {result_df['ageBracket'].nunique()}")
    print(f"Sex categories: {result_df['sex'].nunique()}")
    print(f"Total records: {len(result_df)}")
    
    return result_df

# Command line usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean.py input_file.csv [output_file.csv]")
        print("Available functions: clean_pg, clean_pas")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # determine which function to call based on filename or additional argument
    if 'population-growth' in input_file:
        clean_pg(input_file, output_file)
    elif 'demographics' in input_file:
        clean_pas(input_file, output_file)
    else:
        print("Cannot determine which cleaning function to use.")
        print("Please specify a file with 'population-growth' or 'demographics' in the name.")
        print(f"Your file: {input_file}")
        sys.exit(1)