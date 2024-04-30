import os
import ast
from airflow.decorators import dag, task
from airflow.utils.dates import datetime
import pandas as pd
from datetime import datetime, timedelta
import time
import pandas as pd
import requests
import concurrent.futures
from tqdm import tqdm
from uszipcode import SearchEngine
import us
import re
import warnings

from source.data_transformation_utils import clean_state_data, combine_agoda_data, enrich_combined_agoda_data, transform_and_process_raw_booking_data, clean_and_combine_accomodation_data
from source.db_utils import create_database, check_table_exists, store_df_to_db, store_csv_to_db
from source.scrape_utils import booking_scraper

warnings.filterwarnings("ignore")

default_args = {
    "owner": "airflow",
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}

# We set the schedule to be None here but normally we would set it to a time period appropriate for data refreshes.

@dag(
    dag_id='project_dag',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['project']
)

def project_dag():

    # Extract
    @task(task_id='scrape_booking_data')
    def scrape_booking_data():
        raw_booking_filepath = booking_scraper()
        return raw_booking_filepath
    
    @task(task_id='ingest_state_data')
    def ingest_state_data():
        raw_state_table_name = "raw_state_table"
        state_data_filepath = "/opt/airflow/dags/data/state/raw_state_table.csv"

        store_csv_to_db(state_data_filepath, raw_state_table_name)

        return raw_state_table_name
    
    @task(task_id='ingest_and_combine_agoda_data')
    def ingest_and_combine_agoda_data():
        combined_raw_agoda_table_name = "combined_raw_agoda_table"
        raw_agoda_data_directory = "/opt/airflow/dags/data/agoda"

        agoda_df = combine_agoda_data(raw_agoda_data_directory)
        store_df_to_db(agoda_df, combined_raw_agoda_table_name)
        return combined_raw_agoda_table_name

    @task(task_id='ingest_booking_data')
    def ingest_booking_data(raw_booking_filepath):
        raw_booking_table_name = "raw_booking_table"

        store_csv_to_db(raw_booking_filepath, raw_booking_table_name)
        return raw_booking_table_name

    # Transformation

    @task(task_id='enrich_agoda_data')
    def enrich_agoda_data(combined_raw_agoda_table_name):
        cleaned_agoda_table_name = "cleaned_agoda_table"
        cleaned_agoda_df = enrich_combined_agoda_data(combined_raw_agoda_table_name)
        store_df_to_db(cleaned_agoda_df, cleaned_agoda_table_name)
        return cleaned_agoda_table_name
    
    @task(task_id='transform_and_process_booking_data')
    def transform_and_process_booking_data(raw_booking_table_name):
        cleaned_booking_table_name = "cleaned_booking_table"
        cleaned_booking_df = transform_and_process_raw_booking_data(raw_booking_table_name)
        store_df_to_db(cleaned_booking_df, cleaned_booking_table_name)
        return cleaned_booking_table_name

    # Load

    @task(task_id='transform_and_load_state_data')
    def transform_state_data(raw_state_table_name):
        clean_state_table_name = "state_table"

        clean_state_df = clean_state_data(raw_state_table_name)
        store_df_to_db(clean_state_df, clean_state_table_name)
        if not check_table_exists(clean_state_table_name):
            create_database(clean_state_table_name)

        return clean_state_table_name

    @task(task_id='combine_and_load_accomodation_data')
    def combine_accomodation_data(cleaned_agoda_table_name, cleaned_booking_table_name):
        cleaned_accomodation_name = "accomodation_table"
        cleaned_accomodation_name_df = clean_and_combine_accomodation_data(cleaned_agoda_table_name, cleaned_booking_table_name)
        if not check_table_exists(cleaned_accomodation_name):
            create_database(cleaned_accomodation_name)
        store_df_to_db(cleaned_accomodation_name_df, cleaned_accomodation_name)
        return cleaned_accomodation_name

    # Extraction
    raw_booking_data_filepath = scrape_booking_data()
    raw_state_table_name = ingest_state_data()
    raw_booking_table_name = ingest_booking_data(raw_booking_data_filepath)
    combined_raw_agoda_table_name = ingest_and_combine_agoda_data()

    # Transformation
    cleaned_agoda_table_name = enrich_agoda_data(combined_raw_agoda_table_name)
    cleaned_booking_table_name = transform_and_process_booking_data(raw_booking_table_name)

    # Final Clean and Load
    cleaned_state_data = transform_state_data(raw_state_table_name)
    cleaned_accomodation_data = combine_accomodation_data(cleaned_agoda_table_name, cleaned_booking_table_name)

project_dag_instance = project_dag()