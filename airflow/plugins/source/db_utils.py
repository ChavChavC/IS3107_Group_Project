from datetime import datetime

from sqlalchemy import create_engine, inspect
import pandas as pd

# Need to add local mySQL password here
engine_password = ""

def check_table_exists(table_name):
    """
    Function to check if a table exists in the database.
    
    Parameters:
        engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine object for database connection.
        table_name (str): Name of the table to check existence for.
        
    Returns:
        bool: True if the table exists, False otherwise.
    """
    engine = create_engine(f'mysql+pymysql://root:{engine_password}@host.docker.internal/is3107')
    inspector = inspect(engine)
    engine.dispose()
    return inspector.has_table(table_name)

def create_database(table_name):

    engine = create_engine(f'mysql+pymysql://root:{engine_password}@host.docker.internal/is3107')

    if table_name == "accomodation_table":
        table_creation_string = f"""
                CREATE TABLE accomodation_table (
                    hotel_id INT AUTO_INCREMENT PRIMARY KEY,
                    hotel_name VARCHAR(255),
                    overall_rating DOUBLE,
                    total_num_of_reviews INTEGER,
                    latitude VARCHAR(255),
                    longitude VARCHAR(255),
                    description TEXT,
                    popular_facilities TEXT,
                    region_code VARCHAR(255),
                    location DOUBLE,
                    service DOUBLE,
                    cleanliness DOUBLE,
                    value DOUBLE,
                    facilities DOUBLE,
                    restaurant INT,
                    shopping_mall INT,
                    tourist_attraction INT,
                    cafe INT,
                    bar INT,
                    supermarket INT,
                    park INT,
                    point_of_interest INT,
                    lodging INT,
                    museum INT
                );
        """
    else:
        table_creation_string = f"""
                CREATE TABLE state_table (
                        state_code VARCHAR(255) PRIMARY KEY,
                        state_name VARCHAR(255),
                        abbrev VARCHAR(255),
                        population_size INTEGER,
                        median_household_income DOUBLE,
                        median_age DOUBLE,
                        median_housing_value DOUBLE,
                        employment_status_num INTEGER
                    );
        """
    
    with engine.connect() as connection:
        connection.execute(table_creation_string)

    engine.dispose()

    return

def store_csv_to_db(filepath, table_name):

    engine = create_engine(f'mysql+pymysql://root:{engine_password}@host.docker.internal/is3107')

    df = pd.read_csv(filepath)
    df.to_sql(table_name, con=engine, if_exists='append', index=False) 

    engine.dispose()

    return 

def store_df_to_db(df, table_name):

    engine = create_engine(f'mysql+pymysql://root:{engine_password}@host.docker.internal/is3107')

    df.to_sql(table_name, con=engine, if_exists='append', index=False) 

    engine.dispose()

    return 

def store_cleaned_df_to_db(df, table_name):

    engine = create_engine(f'mysql+pymysql://root:{engine_password}@host.docker.internal/is3107')

    if not check_table_exists(table_name):
        create_database(table_name)

    df.to_sql(table_name, con=engine, if_exists='append', index=False) 

    engine.dispose()

    return 

def retrieve_df(query):

    engine = create_engine(f'mysql+pymysql://root:{engine_password}@host.docker.internal/is3107')
    df = pd.read_sql(query, engine)
    return df