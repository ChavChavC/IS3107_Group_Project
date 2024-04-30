import os
import pandas as pd
import ast
import requests

from source.db_utils import retrieve_df
from source.hotel_utils import enrich_agoda_data, enrich_booking_data

# Need a Google Places API Key here
api_key = ""

def combine_agoda_data(raw_agoda_data_filepath):
    dfs = []
    for filename in os.listdir(raw_agoda_data_filepath):
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            filepath = os.path.join(raw_agoda_data_filepath, filename)
            # Read the Excel file into a DataFrame
            df = pd.read_excel(filepath)
            # Add a column 'region_shortform' with the filename as its value
            df['region_shortform'] = filename[:-5]  # Removing extension (.xlsx or .xls)
            # Rename columns as per requirements
            df.rename(columns={'Hotel Name': 'hotel_name',
                            'Description': 'description',
                            'Overall Rating': 'overall_rating',
                                'Rating Count': 'total_num_of_reviews',
                            'Facilities': 'popular_facilities'}, inplace=True)
            # Convert 'Facilities' column from list to string
            df['popular_facilities'] = df['popular_facilities'].apply(lambda x: ', '.join(eval(x)))
            # Drop the 'Hotel Link' column
            df.drop(columns=['Hotel Link'], inplace=True)
            # Extract keys from the 'Individual Ratings' column and create separate columns
            individual_ratings = df['Individual Ratings'].apply(lambda x: ast.literal_eval(x))
            for key in individual_ratings.iloc[0].keys():
                df[key.lower()] = individual_ratings.apply(lambda x: x.get(key, None))
            # Append the DataFrame to the list
            df.drop(columns=['Individual Ratings'], inplace=True)
            room_columns = [col for col in df.columns if 'room' in col.lower()]
            df.drop(columns=room_columns, inplace=True)
            df['total_num_of_reviews'] = df['total_num_of_reviews'].str.replace(',', '').str.extract('(\d+)').astype(int)
            df.rename(columns={'value for money': 'value'}, inplace=True)
            dfs.append(df)
    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(dfs, ignore_index=True)

    return combined_df

def enrich_combined_agoda_data(combined_raw_agoda_table_name):

    query = f"""
            SELECT *
            FROM {combined_raw_agoda_table_name}
            """

    raw_combined_agoda_data = retrieve_df(query)
    enriched_agoda_data = enrich_agoda_data(api_key, raw_combined_agoda_data)
    cleaned_agoda_data = pd.merge(raw_combined_agoda_data, enriched_agoda_data, left_on='hotel_name', right_on="Original Hotel Name", how='left')

    cleaned_agoda_data['latitude'] = pd.to_numeric(cleaned_agoda_data['latitude'], errors='coerce')
    cleaned_agoda_data['longitude'] = pd.to_numeric(cleaned_agoda_data['longitude'], errors='coerce')

    cleaned_agoda_data = cleaned_agoda_data[(cleaned_agoda_data['latitude'] >= 25) & 
                                        (cleaned_agoda_data['latitude'] <= 49) & 
                                        (cleaned_agoda_data['longitude'] >= -125) & 
                                        (cleaned_agoda_data['longitude'] <= -67)]
    
    return cleaned_agoda_data

def transform_and_process_raw_booking_data(raw_booking_table_name):

    query = f"""
            SELECT *
            FROM {raw_booking_table_name}
            """
    
    raw_booking_data = retrieve_df(query)
    raw_booking_data['lat/long'] = raw_booking_data['lat/long'].apply(lambda x: ast.literal_eval(x))
    raw_booking_data['latitude'] = raw_booking_data['lat/long'].apply(lambda x: x[0])
    raw_booking_data['longitude'] = raw_booking_data['lat/long'].apply(lambda x: x[1])
    raw_booking_data.drop(columns=['lat/long'], inplace=True)

    enriched_booking_data = enrich_booking_data(api_key, raw_booking_data)

    cleaned_booking_data = pd.merge(raw_booking_data, enriched_booking_data, left_on='hotel_name', right_on='Hotel Name', how='left')

    cleaned_booking_data['latitude_x'] = pd.to_numeric(cleaned_booking_data['latitude_x'], errors='coerce')
    cleaned_booking_data['longitude_x'] = pd.to_numeric(cleaned_booking_data['longitude_x'], errors='coerce')

    cleaned_booking_data = cleaned_booking_data[(cleaned_booking_data['latitude_x'] >= 25) & 
                                    (cleaned_booking_data['latitude_x'] <= 49) & 
                                    (cleaned_booking_data['longitude_x'] >= -125) & 
                                    (cleaned_booking_data['longitude_x'] <= -67)]

    return cleaned_booking_data

def clean_and_combine_accomodation_data(cleaned_agoda_table_name, cleaned_booking_table_name):

    query = f"""
            SELECT hotel_name,
                overall_rating,
                total_num_of_reviews,
                latitude,
                longitude,
                description,
                popular_facilities,
                region_shortform AS region_code,
                location,
                service,
                cleanliness,
                value,
                facilities,
                restaurant,
                shopping_mall,
                tourist_attraction,
                cafe,
                bar,
                supermarket,
                park,
                point_of_interest,
                lodging,
                museum
            FROM {cleaned_agoda_table_name}
            UNION
            SELECT hotel_name,
                overall_rating,
                total_num_of_reviews,
                latitude_x AS latitude,
                longitude_x AS longitude,
                description,
                popular_facilities,
                region_shortform AS region_code,
                location,
                service,
                cleanliness,
                value,
                facilities,
                restaurant,
                shopping_mall,
                tourist_attraction,
                cafe,
                bar,
                supermarket,
                park,
                point_of_interest,
                lodging,
                museum
            FROM {cleaned_booking_table_name}
            """
    combined_data = retrieve_df(query)

    return combined_data

def clean_state_data(raw_state_table_name):

    query = f"""
            SELECT * 
            FROM {raw_state_table_name}
            """
    
    state_df = retrieve_df(query)

    # Retrieving State Code to Map to
    url = "https://api.census.gov/data/2019/acs/acs1/subject"
    params = {
        'get': 'NAME,S1901_C01_012E',
        'for': 'state:*'
    }
    response = requests.get(url, params=params)
    data = response.json()
    state_info = []
    for row in data[1:]:
        state_name, _ , state_code = row
        state_info.append({'state_name': state_name,'state_code': state_code})

    state_code_df = pd.DataFrame(state_info)
    state_df = pd.merge(state_df, state_code_df[['state_name', 'state_code']], on=['state_name'], how= "left")

    # Retrieving Population Data
    url_population = "https://api.census.gov/data/2021/acs/acsse"
    params_population = {
        'get': 'K200104_001E',
        'for': 'state:*',
        'key': '869af8761cf9a743099afcbd9f04be4389a3a854'
    }
    response_population = requests.get(url_population, params=params_population)
    data_population = response_population.json()
    population_size = {}
    for row in data_population[1:]:
        state_population, state_code = row
        population_size[state_code] = int(state_population)

    population_df = pd.DataFrame(population_size.items(), columns=['state_code', 'population_size'])
    state_df = pd.merge(state_df, population_df, on=['state_code'], how= "left")

    # Fetch data for median household income
    url_income = "https://api.census.gov/data/2021/acs/acsse"
    params_income = {
        'get': 'K201901_001E',
        'for': 'state:*',
        'key': '869af8761cf9a743099afcbd9f04be4389a3a854'
    }
    response_income = requests.get(url_income, params=params_income)
    data_income = response_income.json()
    median_household_incomes = {}
    for row in data_income[1:]:
        state_income, state_code = row
        median_household_incomes[state_code] = int(state_income)
    income_df = pd.DataFrame(median_household_incomes.items(), columns=['state_code', 'median_household_income'])
    state_df = pd.merge(state_df, income_df, on=['state_code'], how= "left")
   
    # Fetch data for median age
    url_age = "https://api.census.gov/data/2021/acs/acsse"
    params_age = {
        'get': 'K200103_001E',
        'for': 'state:*',
        'key': '869af8761cf9a743099afcbd9f04be4389a3a854'
    }
    response_age = requests.get(url_age, params=params_age)
    data_age = response_age.json()
    median_age = {}
    for row in data_age[1:]:
        state_age, state_code = row
        median_age[state_code] = float(state_age)
    age_df = pd.DataFrame(median_age.items(), columns=['state_code', 'median_age'])
    state_df = pd.merge(state_df, age_df, on=['state_code'], how= "left")

    # Fetch data for average housing value
    url_housing = "https://api.census.gov/data/2021/acs/acsse"
    params_housing = {
        'get': 'K202509_001E',
        'for': 'state:*',
        'key': '869af8761cf9a743099afcbd9f04be4389a3a854'
    }
    response_housing = requests.get(url_housing, params=params_housing)
    data_housing = response_housing.json()
    housing_value = {}
    for row in data_housing[1:]:
        state_housing_value, state_code = row
        housing_value[state_code] = int(state_housing_value)
    median_housing_value_df = pd.DataFrame(housing_value.items(), columns=['state_code', 'median_housing_value'])
    state_df = pd.merge(state_df, median_housing_value_df, on=['state_code'], how= "left")

    url = "https://api.census.gov/data/2021/acs/acsse"

    params = {
        # Employment Status
        'get': 'K202301_001E',
        'for': 'state:*',
        'key': '869af8761cf9a743099afcbd9f04be4389a3a854'
    }

    response = requests.get(url, params=params)
    data = response.json()

    employment_status = {}
    for row in data[1:]:
        employment_status_num, state_code = row
        employment_status[state_code] = int(employment_status_num)

    # Creating a DataFrame from the dictionary
    employment_df = pd.DataFrame(employment_status.items(), columns=['state_code', 'employment_status_num'])
    state_df = pd.merge(state_df, employment_df, on=['state_code'], how= "left")

    state_df.drop(columns=['state_code'], inplace=True)
    state_df.rename(columns={'code': 'state_code'}, inplace=True)

    return state_df