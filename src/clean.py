#!/usr/bin/env python3
"""
tabular output csv cleanup script

Takes csv files from existing City Scan tabular output and interim Scan Calculation Sheet data outputs and cleans up formatting and makes additional calculations so that the output is ready for visualization, returning new csv files:

"""

import pandas as pd
import numpy as np
import rasterio
import os
import sys
from typing import Optional

# population growth
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

# population age sex
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

# urban extent and change
def clean_uba(input_file, output_file=None):
    """
    clean up the urban built area csv file (i.e., 20XX-0X-country-city_other_02-process-output_tabular_city_wsf_stats.csv) for visualization as uba.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file
    output_file : str, optional
        Path for output.
    """
    
    # read the urban built area CSV file
    df = pd.read_csv(input_file)
    
    # sort by year to ensure correct order
    df = df.sort_values('year').reset_index(drop=True)
    
    # create new dataframe with desired structure
    result_df = pd.DataFrame({
        'year': range(1, len(df) + 1),  # sequential numbering starting from 1
        'yearName': df['year'],
        'uba': df['cumulative sq km'].round(2)  # round to 2 decimal places
    })
    
    # calculate urban built area growth percentage
    # growth percentage = ((current_year - previous_year) / previous_year) * 100
    result_df['ubaGrowthPercentage'] = result_df['uba'].pct_change() * 100
    
    # round to 3 decimal places to match your example
    result_df['ubaGrowthPercentage'] = result_df['ubaGrowthPercentage'].round(3)
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/uba.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Years covered: {result_df['yearName'].min()} - {result_df['yearName'].max()}")
    print(f"Total data points: {len(result_df)}")
    print(f"UBA range: {result_df['uba'].min():.2f} - {result_df['uba'].max():.2f} sq km")
    
    return result_df

# land cover
def clean_lc(input_file, output_file=None):
    """
    clean up the 20XX-02-country-city_02-process-output_tabular_city_lc.csv file for visualization as lc.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file (land cover data)
    output_file : str, optional
        Path for output.
    """
    
    # read the land cover CSV file
    df = pd.read_csv(input_file)
    
    # remove rows where Pixel Count is 0 (no coverage for that land type)
    # also remove any "total" or summary rows that might be in the data
    df_filtered = df[
        (df['Pixel Count'] > 0) & 
        (~df['Land Cover Type'].str.contains('total', case=False, na=False))
    ].copy()
    
    # calculate total pixels for percentage calculation
    total_pixels = df_filtered['Pixel Count'].sum()
    
    # create new dataframe with desired structure
    result_df = pd.DataFrame({
        'lcType': df_filtered['Land Cover Type'],
        'pixelCount': df_filtered['Pixel Count'].round(0).astype(int),
        'pixelTotal': total_pixels,
        'percentage': ((df_filtered['Pixel Count'] / total_pixels) * 100).round(2)
    })
    
    # sort by percentage in descending order (most common land cover first)
    result_df = result_df.sort_values('percentage', ascending=False).reset_index(drop=True)
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/lc.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Land cover types: {len(result_df)}")
    print(f"Total pixels analyzed: {total_pixels:,.0f}")
    print(f"Percentage coverage verification: {result_df['percentage'].sum():.1f}% (should be ~100%)")
    
    # identify dominant land cover types
    dominant_type = result_df.iloc[0]
    print(f"Dominant land cover: {dominant_type['lcType']} ({dominant_type['percentage']:.1f}%)")
    
    return result_df

# population urban growth (urban development dynamics matrix)
def clean_pug(pg_file=None, uba_file=None, output_file=None):
    """
    clean up and merge population growth (pg.csv) and urban built area (uba.csv) data 
    for visualization as pug.csv (population urban growth ratio for urban development dynamics matrix).
    
    parameters:
    -----------
    pg_file : str, optional
        Path to the population growth CSV file (default: 'data/processed/pg.csv')
    uba_file : str, optional
        Path to the urban built area CSV file (default: 'data/processed/uba.csv')
    output_file : str, optional
        Path for output (default: 'data/processed/pug.csv')
    """
    
    # set default file paths if not provided
    if pg_file is None:
        pg_file = 'data/processed/pg.csv'
    if uba_file is None:
        uba_file = 'data/processed/uba.csv'
    
    # read pg.csv and uba.csv
    try:
        pg_df = pd.read_csv(pg_file)
        print(f"✅ Successfully loaded population growth data: {len(pg_df)} records")
    except FileNotFoundError:
        raise FileNotFoundError(f"Population growth file not found: {pg_file}")
    except Exception as e:
        raise Exception(f"Error reading population growth file: {e}")
    
    try:
        uba_df = pd.read_csv(uba_file)
        print(f"✅ Successfully loaded urban built area data: {len(uba_df)} records")
    except FileNotFoundError:
        raise FileNotFoundError(f"Urban built area file not found: {uba_file}")
    except Exception as e:
        raise Exception(f"Error reading urban built area file: {e}")
    
    # merge pg_df and uba_df on yearName to create pug
    pug_df = pd.merge(pg_df, uba_df, on='yearName', how='inner')
    print(f"✅ Successfully merged datasets: {len(pug_df)} overlapping years")
    
    if len(pug_df) == 0:
        raise ValueError("No overlapping years found between population growth and urban built area data")
    
    # calculate density (population per unit area)
    pug_df['density'] = (pug_df['population'] / pug_df['uba']).round(3)
    
    # calculate population-urban growth percentage ratio
    # handle division by zero cases
    mask = pug_df['ubaGrowthPercentage'] != 0
    pug_df['populationUrbanGrowthRatio'] = None
    pug_df.loc[mask, 'populationUrbanGrowthRatio'] = (
        pug_df.loc[mask, 'populationGrowthPercentage'] / 
        pug_df.loc[mask, 'ubaGrowthPercentage']
    ).round(3)
    
    # reorder columns to match expected output structure
    expected_columns = ['yearName', 'population', 'populationGrowthPercentage', 'year', 'uba', 
                       'ubaGrowthPercentage', 'density', 'populationUrbanGrowthRatio']
    
    # ensure all expected columns exist
    missing_columns = [col for col in expected_columns if col not in pug_df.columns]
    if missing_columns:
        print(f"⚠️  Warning: Missing expected columns: {missing_columns}")
    
    # reorder existing columns
    available_columns = [col for col in expected_columns if col in pug_df.columns]
    pug_df = pug_df[available_columns]
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/pug.csv'
    
    # save pug_df for population urban growth data to CSV
    pug_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Years covered: {pug_df['yearName'].min()} - {pug_df['yearName'].max()}")
    print(f"Total data points: {len(pug_df)}")
    print(f"Population range: {pug_df['population'].min():,} - {pug_df['population'].max():,}")
    print(f"UBA range: {pug_df['uba'].min():.2f} - {pug_df['uba'].max():.2f}")
    print(f"Density range: {pug_df['density'].min():.1f} - {pug_df['density'].max():.1f}")
    
    # check for any missing ratios
    missing_ratios = pug_df['populationUrbanGrowthRatio'].isna().sum()
    if missing_ratios > 0:
        print(f"⚠️  Note: {missing_ratios} missing growth ratios (likely due to zero UBA growth)")
    
    return pug_df

# photovoltaic (monthly max pv potential)
def clean_pv(input_file, output_file=None):
    """
    clean up the monthly-pv.csv file for visualization as pv.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file (monthly-pv.csv)
    output_file : str, optional
        Path for output.
    """
    
    # read the monthly photovoltaic CSV file
    df = pd.read_csv(input_file)
    
    # PV condition classification based on World Bank Global Solar Atlas standards
    # Reference: World Bank Global Photovoltaic Power Potential by Country study
    # https://www.worldbank.org/en/topic/energy/publication/solar-photovoltaic-power-potential-by-country
    def categorize_pv_condition(maxpv):
        """
        PV condition classification based on World Bank/Solargis Global Solar Atlas:
        - Excellent: >4.5 kWh/kWp
        - Favorable: 3.5-4.5 kWh/kWp
        - Less than Favorable: <3.5 kWh/kWp
        """
        if pd.isna(maxpv):
            return 'Unknown'
        elif maxpv > 4.5:
            return 'Excellent'
        elif maxpv >= 3.5:
            return 'Favorable'
        else:
            return 'Less than Favorable'
    
    # create new dataframe with desired structure
    # extract max values for each month to create the simplified pv.csv structure
    result_df = pd.DataFrame({
        'month': df['month'],
        'monthName': df['month'].map({
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }),
        'maxPv': df['max'].round(2),  # round to 2 decimal places to match expected output
        'condition': df['max'].apply(categorize_pv_condition)
    })
    
    # sort by month to ensure proper order
    result_df = result_df.sort_values('month').reset_index(drop=True)
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/pv.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Months covered: {len(result_df)} months (full year)")
    print(f"PV potential range: {result_df['maxPv'].min():.2f} - {result_df['maxPv'].max():.2f}")
    print(f"Peak month: {result_df.loc[result_df['maxPv'].idxmax(), 'monthName']} ({result_df['maxPv'].max():.2f})")
    print(f"Lowest month: {result_df.loc[result_df['maxPv'].idxmin(), 'monthName']} ({result_df['maxPv'].min():.2f})")
    
    # condition distribution (World Bank classification)
    condition_counts = result_df['condition'].value_counts()
    print(f"PV condition distribution (World Bank standards):")
    for condition in ['Excellent', 'Favorable', 'Less than Favorable']:
        count = condition_counts.get(condition, 0)
        print(f"  {condition}: {count} months")
    
    # calculate seasonal insights
    summer_months = result_df[result_df['month'].isin([6, 7, 8])]  # Jun, Jul, Aug
    winter_months = result_df[result_df['month'].isin([12, 1, 2])]  # Dec, Jan, Feb
    
    summer_avg = summer_months['maxPv'].mean()
    winter_avg = winter_months['maxPv'].mean()
    seasonal_variation = ((summer_avg - winter_avg) / winter_avg) * 100
    
    print(f"Summer average (Jun-Aug): {summer_avg:.2f}")
    print(f"Winter average (Dec-Feb): {winter_avg:.2f}")
    print(f"Seasonal variation: {seasonal_variation:.1f}% higher in summer")
    
    return result_df

# photovoltaic (% area with different pv conditions - "Excellent (4+5)","Favorable (3.5-4.5)","Less than Favorable (<3.5)")
def clean_pv_area(input_tif_file: str, output_file: Optional[str] = None) -> pd.DataFrame:
    """
    process photovoltaic potential TIF (i.e., solar.tif) data into cleaned csv, pv_area.csv for visualization.
    
    Parameters:
    -----------
    input_tif_file : str
        Path to the input TIF file (photovoltaic potential data)
    output_file : str, optional
        Path for output CSV file. If None, saves to 'data/processed/pv_area.csv'
    
    Returns:
    --------
    pd.DataFrame
        Cleaned dataframe with columns: bin, condition, count, percentage
    """
    
    try:
        # read the TIF file
        with rasterio.open(input_tif_file) as src:
            # read the data as a numpy array
            pv_data = src.read(1)  # read first band
            
            # get valid data (exclude "NoData" values)
            nodata_value = src.nodata
            if nodata_value is not None:
                valid_data = pv_data[pv_data != nodata_value]
            else:
                # if no explicit, "NoData" value, exclude NaN and very large/small values
                valid_data = pv_data[~np.isnan(pv_data)]
                valid_data = valid_data[np.isfinite(valid_data)]
    
    except Exception as e:
        raise Exception(f"Error reading TIF file {input_tif_file}: {e}")
    
    # define bins and conditions based on photovoltaic potential values
    bins = [
        {"range": "(0-3.5)", "condition": "Less than Favorable", "min_val": 0, "max_val": 3.5},
        {"range": "(3.5-4.5)", "condition": "Favorable", "min_val": 3.5, "max_val": 4.5},
        {"range": "4.5+", "condition": "Excellent", "min_val": 4.5, "max_val": float('inf')}
    ]
    
    # count pixels in each bin
    bin_data = []
    total_pixels = len(valid_data)
    
    for bin_info in bins:
        if bin_info["max_val"] == float('inf'):
            # for the "4.5+" (i.e., "Excellent") category
            count = np.sum(valid_data >= bin_info["min_val"])
        else:
            # for ranges with upper bounds
            count = np.sum((valid_data >= bin_info["min_val"]) & (valid_data < bin_info["max_val"]))
        
        bin_data.append({
            'bin': bin_info["range"],
            'condition': bin_info["condition"],
            'count': int(count),
            'percentage': round((count / total_pixels) * 100, 2) if total_pixels > 0 else 0
        })
    
    # create dataframe
    result_df = pd.DataFrame(bin_data)
    
    # filter out bins with zero count (optional)
    # result_df = result_df[result_df['count'] > 0].copy()
    
    # create output filename if not provided
    if output_file is None:
        # ensure the "processed" directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/pv_area.csv'
    
    # save cleaned data
    result_df.to_csv(output_file, index=False)
    
    # basic validation and reporting
    total_count = result_df['count'].sum()
    percentage_sum = result_df['percentage'].sum()
    
    print(f"Cleaned PV data saved to: {output_file}")
    print(f"PV potential bins: {len(result_df)}")
    print(f"Total pixels analyzed: {total_count:,.0f}")
    print(f"Percentage coverage verification: {percentage_sum:.1f}% (should be ~100%)")
    
    # ID dominant condition
    if len(result_df) > 0:
        dominant_bin = result_df.loc[result_df['percentage'].idxmax()]
        print(f"Dominant PV condition: {dominant_bin['condition']} - {dominant_bin['bin']} ({dominant_bin['percentage']:.1f}%)")
    
    return result_df

# flooding
def clean_flood(input_file, output_dir=None):
    """
    clean up the 20XX-0X-country-city_02-process-output_tabular_city_flood_wsf.csv file and create separate output files for each flood type.
    Creates fu.csv (fluvial), pu.csv (pluvial), cu.csv (coastal), and comb.csv (combined)
    based on available data in the input file.

    Note: flood-events.csv is not included as in input file because the csv is already cleaned and ready for visualization.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file (flood data)
    output_dir : str, optional
        Directory for output files (default: 'data/processed/')
    """
    
    # read the flood data CSV file
    df = pd.read_csv(input_file)
    
    # set default output directory
    if output_dir is None:
        import os
        output_dir = 'data/processed'
        os.makedirs(output_dir, exist_ok=True)
    
    # identify available flood types based on column names
    available_flood_types = {}
    
    # check for each flood type (looking for columns ending with _2020)
    if any('coastal_2020' in col for col in df.columns):
        available_flood_types['coastal'] = 'coastal_2020'
    if any('fluvial_2020' in col for col in df.columns):
        available_flood_types['fluvial'] = 'fluvial_2020'  
    if any('pluvial_2020' in col for col in df.columns):
        available_flood_types['pluvial'] = 'pluvial_2020'
    if any('comb_2020' in col for col in df.columns):
        available_flood_types['combined'] = 'comb_2020'
    
    print(f"Available flood types: {list(available_flood_types.keys())}")
    
    created_files = []
    
    # process each available flood type
    flood_mappings = {
        'fluvial': ('fu', 'fu.csv'),
        'pluvial': ('pu', 'pu.csv'), 
        'coastal': ('cu', 'cu.csv'),
        'combined': ('comb', 'comb.csv')
    }
    
    for flood_type, column_name in available_flood_types.items():
        if flood_type in flood_mappings:
            short_name, filename = flood_mappings[flood_type]
            
            # create dataframe for this flood type
            result_df = pd.DataFrame({
                'year': range(1, len(df) + 1),  # sequential numbering starting from 1
                'yearName': df['year'],  # actual year from input
                short_name: df[column_name].round(2)  # rounded flood values
            })
            
            # sort by year to ensure correct order
            result_df = result_df.sort_values('yearName').reset_index(drop=True)
            
            # save to CSV
            output_path = os.path.join(output_dir, filename)
            result_df.to_csv(output_path, index=False)
            created_files.append(filename)
            
            print(f"✅ Created {filename}: {len(result_df)} records")
            print(f"   Year range: {result_df['yearName'].min()} - {result_df['yearName'].max()}")
            print(f"   {short_name.upper()} range: {result_df[short_name].min():.2f} - {result_df[short_name].max():.2f}")
    
    # summary report
    print(f"\nFlood Risk Data Processing Summary:")
    print(f"- Input file: {input_file}")
    print(f"- Output directory: {output_dir}")
    print(f"- Files created: {', '.join(created_files)}")
    print(f"- Missing flood types: {set(['fluvial', 'pluvial', 'coastal', 'combined']) - set(available_flood_types.keys())}")
    
    # data quality insights
    if len(available_flood_types) > 1:
        print(f"\nFlood Risk Analysis:")
        
        # compare flood types if multiple are available
        for flood_type, column_name in available_flood_types.items():
            avg_risk = df[column_name].mean()
            max_risk = df[column_name].max()
            min_risk = df[column_name].min()
            trend = df[column_name].iloc[-1] - df[column_name].iloc[0]  # latest - earliest
            
            print(f"- {flood_type.capitalize()} flood risk:")
            print(f"  Average: {avg_risk:.2f}, Range: {min_risk:.2f} - {max_risk:.2f}")
            print(f"  Trend (1985-2015): {trend:+.2f} ({'+increase' if trend > 0 else 'decrease' if trend < 0 else 'stable'})")
        
        # identify highest risk type
        latest_year_risks = {}
        for flood_type, column_name in available_flood_types.items():
            latest_year_risks[flood_type] = df[column_name].iloc[-1]
        
        highest_risk_type = max(latest_year_risks, key=latest_year_risks.get)
        print(f"- Dominant risk type (2015): {highest_risk_type.capitalize()} ({latest_year_risks[highest_risk_type]:.2f})")
    
    return created_files

# elevation
def clean_e(input_file, output_file=None):
    """
    clean up the elevation csv file for visualization as e.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file (elevation data)
    output_file : str, optional
        Path for output.
    """
    
    # read the elevation csv file
    df = pd.read_csv(input_file)
    
    # remove any total/summary rows and zero-count rows
    df_filtered = df[
        (~df['Bin'].astype(str).str.contains('total', case=False, na=False)) &
        (df['Count'] > 0)
    ].copy()
    
    # sort elevation bins properly (handles different elevation ranges for different cities)
    def extract_elevation_value(bin_str):
        """Extract numeric value from elevation bin for sorting"""
        try:
            # negative elevations (e.g., "-45")
            if bin_str.startswith('-'):
                return float(bin_str)
            # range bins (e.g., "40-85", "130-175")
            elif '-' in bin_str:
                return float(bin_str.split('-')[0])
            # single values
            else:
                return float(bin_str)
        except (ValueError, AttributeError):
            # if parsing fails, return a very high number to put it at the end
            return 9999
    
    # add sorting column and sort by elevation
    df_filtered['sort_value'] = df_filtered['Bin'].apply(extract_elevation_value)
    df_filtered = df_filtered.sort_values('sort_value').reset_index(drop=True)
    
    # calculate total count for percentage calculation
    total_count = df_filtered['Count'].sum()
    
    # create new df with desired structure for Observable Plot
    result_df = pd.DataFrame({
        'bin': df_filtered['Bin'],
        'count': df_filtered['Count'].astype(int),
        'percentage': ((df_filtered['Count'] / total_count) * 100).round(2)
    })
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/e.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Elevation bins: {len(result_df)}")
    print(f"Elevation range: {result_df['bin'].iloc[0]} to {result_df['bin'].iloc[-1]}")
    print(f"Total area analyzed: {total_count:,.0f} pixels")
    print(f"Percentage coverage verification: {result_df['percentage'].sum():.1f}% (should be ~100%)")
    
    # identify elevation distribution
    dominant_bin = result_df.loc[result_df['percentage'].idxmax()]
    print(f"Dominant elevation range: {dominant_bin['bin']} ({dominant_bin['percentage']:.1f}%)")
    
    # elevation range analysis (dynamic thresholds)
    major_bins = result_df[result_df['percentage'] >= 10]  # bins with ≥10% coverage
    if len(major_bins) > 0:
        print(f"Major elevation ranges (≥10% coverage): {len(major_bins)} bins")
        print(f"Major ranges: {', '.join(major_bins['bin'].tolist())}")
    
    return result_df

# slope
def clean_s(input_file, output_file=None):
    """
    clean up the slope csv file for visualization as s.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file (slope data)
    output_file : str, optional
        Path for output.
    """
    
    # read the slope CSV file
    df = pd.read_csv(input_file)
    
    # remove any total/summary rows and zero-count rows
    df_filtered = df[
        (~df['Bin'].astype(str).str.contains('total', case=False, na=False)) &
        (df['Count'] > 0)
    ].copy()
    
    # sort slope bins properly (slope bins are consistent across cities)
    def extract_slope_value(bin_str):
        """Extract numeric value from slope bin for sorting"""
        try:
            # range bins (e.g., "0-2", "2-5", "5-10")
            if '-' in bin_str:
                return float(bin_str.split('-')[0])
            # single values
            else:
                return float(bin_str)
        except (ValueError, AttributeError):
            # if parsing fails, return a very high number to put it at the end
            return 9999
    
    # add sorting column and sort by slope
    df_filtered['sort_value'] = df_filtered['Bin'].apply(extract_slope_value)
    df_filtered = df_filtered.sort_values('sort_value').reset_index(drop=True)
    
    # calculate total count for percentage calculation
    total_count = df_filtered['Count'].sum()
    
    # create new df
    result_df = pd.DataFrame({
        'bin': df_filtered['Bin'],
        'count': df_filtered['Count'].astype(int),
        'percentage': ((df_filtered['Count'] / total_count) * 100).round(2)
    })
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/s.csv' # save to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Slope bins: {len(result_df)}")
    print(f"Slope range: {result_df['bin'].iloc[0]} to {result_df['bin'].iloc[-1]} degrees")
    print(f"Total area analyzed: {total_count:,.0f} pixels")
    print(f"Percentage coverage verification: {result_df['percentage'].sum():.1f}% (should be ~100%)")
    
    # identify slope distribution
    dominant_bin = result_df.loc[result_df['percentage'].idxmax()]
    print(f"Dominant slope range: {dominant_bin['bin']} degrees ({dominant_bin['percentage']:.1f}%)")
    
    # slope range analysis
    flat_areas = result_df[result_df['bin'].str.contains('0-2|0-5', case=False, na=False)]
    if len(flat_areas) > 0:
        flat_percentage = flat_areas['percentage'].sum()
        print(f"Relatively flat areas (0-5 degrees): {flat_percentage:.1f}%")
    
    steep_areas = result_df[result_df['percentage'] >= 5]  # bins with ≥5% coverage
    if len(steep_areas) > 0:
        print(f"Significant slope ranges (≥5% coverage): {len(steep_areas)} bins")
        print(f"Significant ranges: {', '.join(steep_areas['bin'].tolist())}")
    
    return result_df

def clean_ee(input_file, output_file=None):
    """
    clean up the earthquake-events.csv file for visualization as ee.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file (earthquake-events.csv)
    output_file : str, optional
        Path for output.
    """
    
    # read the earthquake events CSV file
    df = pd.read_csv(input_file)
    
    # extract year from BEGAN column (format appears to be YYYY-MM-DD)
    df['begin_year'] = pd.to_datetime(df['BEGAN'], errors='coerce').dt.year
    
    # create new dataframe with desired structure
    result_df = pd.DataFrame({
        'begin_year': df['begin_year'],
        'distance': df['distance'].round(0).astype('Int64'),  # round to whole numbers, handle NaN
        'eqMagnitude': df['eqMagnitude'].round(1),  # round to 1 decimal place
        'text': df['text'],
        'line1': df['line1'],
        'line2': df['line2'], 
        'line3': df['line3']
    })
    
    # remove rows with missing begin_year (invalid date parsing)
    result_df = result_df.dropna(subset=['begin_year'])
    
    # convert begin_year to integer
    result_df['begin_year'] = result_df['begin_year'].astype(int)
    
    # sort by year to ensure chronological order
    result_df = result_df.sort_values('begin_year').reset_index(drop=True)
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/ee.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Earthquake events: {len(result_df)}")
    print(f"Year range: {result_df['begin_year'].min()} - {result_df['begin_year'].max()}")
    print(f"Magnitude range: {result_df['eqMagnitude'].min():.1f} - {result_df['eqMagnitude'].max():.1f}")
    print(f"Distance range: {result_df['distance'].min()} - {result_df['distance'].max()} km")
    
    return result_df

# fire weather index (fwi)
def clean_fwi(input_file, output_file=None):
    """
    clean up the 20XX-02-country-city_02-process-output_tabular_city_fwi.csv file for visualization as fwi.csv.
    
    parameters:
    -----------
    input_file : str
        Path to the input csv file (fire weather index data)
    output_file : str, optional
        Path for output.
    """
    
    # read the fire weather index CSV file
    df = pd.read_csv(input_file)
    
    # ISO 8601 standard week-to-month mapping
    # Reference: ISO 8601:2004 Data elements and interchange formats
    # Source: https://www.iso.org/standard/40874.html
    def get_month_name_iso(week):
        """ISO 8601 standard week-to-month mapping"""
        if week <= 4:
            return 'Jan'
        elif week <= 9:
            return 'Feb'  
        elif week <= 13:
            return 'Mar'
        elif week <= 17:
            return 'Apr'
        elif week <= 22:
            return 'May'
        elif week <= 26:
            return 'Jun'
        elif week <= 30:
            return 'Jul'
        elif week <= 35:
            return 'Aug'
        elif week <= 39:
            return 'Sep'
        elif week <= 43:
            return 'Oct'
        elif week <= 47:
            return 'Nov'
        else:  # weeks 48-53
            return 'Dec'
    
    # Fire Weather Index danger (i.e., risk) classification

    # Source: https://climate-adapt.eea.europa.eu/en/metadata/indicators/fire-weather-index-monthly-mean-1979-2019
    def categorize_danger(fwi):
        """
        Fire Weather Index danger (i.e., risk) classification system
        Very low: < 5.2, Low: 5.2-11.2, Moderate: 11.2-21.3, 
        High: 21.3-38.0, Very high: 38.0-50.0, Extreme: > 50.0
        """
        if pd.isna(fwi):
            return 'Unknown'
        elif fwi < 5.2:
            return 'Very low'
        elif fwi < 11.2:
            return 'Low'
        elif fwi < 21.3:
            return 'Moderate'
        elif fwi < 38.0:
            return 'High'
        elif fwi < 50.0:
            return 'Very high'
        else:
            return 'Extreme'
    
    # create new dataframe with desired structure
    result_df = pd.DataFrame({
        'week': df['week'],
        'monthName': df['week'].apply(get_month_name_iso),
        'fwi': df['pctile_95'].round(2),  # round to 2 decimal places to match output
        'danger': df['pctile_95'].apply(categorize_danger)
    })
    
    # sort by week to ensure correct order
    result_df = result_df.sort_values('week').reset_index(drop=True)
    
    # create output filename if not provided
    if output_file is None:
        import os
        # ensure the processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        output_file = 'data/processed/fwi.csv' # saves to data/processed folder
            
    # save the cleaned data
    result_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to: {output_file}")
    print(f"Weeks covered: {len(result_df)} weeks")
    print(f"Week range: {result_df['week'].min()} - {result_df['week'].max()}")
    print(f"FWI range: {result_df['fwi'].min():.2f} - {result_df['fwi'].max():.2f}")
    
    # danger level distribution
    danger_counts = result_df['danger'].value_counts()
    print(f"Danger level distribution:")
    for level in ['Very low', 'Low', 'Moderate', 'High', 'Very high', 'Extreme']:
        count = danger_counts.get(level, 0)
        percentage = (count / len(result_df)) * 100
        print(f"  {level}: {count} weeks ({percentage:.1f}%)")
    
    # seasonal fire weather analysis using ISO standard
    seasonal_stats = result_df.groupby('monthName')['fwi'].agg(['mean', 'max']).round(2)
    peak_month = seasonal_stats['max'].idxmax()
    peak_fwi = seasonal_stats['max'].max()
    
    print(f"Peak fire weather month: {peak_month} (max FWI: {peak_fwi:.2f})")
    
    return result_df

# # Command line usage
# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python clean.py input_file.csv [output_file.csv]")
#         print("Available functions: clean_pg, clean_pas, clean_pug, clean_ubaclean_pv, clean_flood, clean_ee, clean_lc")
#         print("For clean_pug: python clean.py pug [pg_file.csv] [uba_file.csv] [output_file.csv]")
#         print("For clean_flood: python clean.py flood_file.csv [output_directory]")
#         sys.exit(1)
    
#     input_file = sys.argv[1]

# Command line usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean.py input_file.csv [output_file.csv]")
        print("Available functions: clean_pg, clean_pas, clean_uba, clean_lc, clean_pug, clean_pv, clean_flood, clean_e, clean_s, clean_ee, clean_fwi")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # determine which function to call based on filename or additional argument
    if 'population-growth' in input_file:
        clean_pg(input_file, output_file)
    elif 'demographics' in input_file:
        clean_pas(input_file, output_file)
    elif 'wsft_stats' in input_file:
        clean_uba(input_file, output_file)
    elif 'lc' in input_file:
        clean_lc(input_file, output_file)
    elif 'pug' in input_file:
        clean_pug(input_file, output_file)
    elif 'monthly-pv' in input_file:
        clean_pv(input_file, output_file)
    elif 'pv_area' in input_file:
        clean_pv_area(input_file, output_file)
    elif 'flood' in input_file:
        clean_flood(input_file, output_file)
    elif 'elevation' in input_file:
        clean_e(input_file, output_file)
    elif 'slope' in input_file:
        clean_s(input_file, output_file)
    elif 'earthquake-events' in input_file: 
        clean_ee(input_file, output_file)
    elif 'fwi' in input_file:   
        clean_fwi(input_file, output_file)

    else:
        print("Cannot determine which cleaning function to use.")
        print("Please specify a file with 'population-growth' or 'demographics' or 'wsf_stats' or 'lc' or 'pug' or 'monthly-pv' or 'pv_area' or 'flood' or 'elevation' or 'slope' or 'earthquake-events' or 'fwi' in the name.")
        print(f"Your file: {input_file}")
        sys.exit(1)