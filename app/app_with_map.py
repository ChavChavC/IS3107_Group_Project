import streamlit as st
import pandas as pd
import nltk
nltk.download('wordnet')  # Downloading WordNet corpus for lemmatization
nltk.download('punkt')  # Downloading Punkt tokenizer for word tokenization
nltk.download('stopwords')  # Downloading stopwords corpus for filtering common words
from nltk.corpus import stopwords  # Importing stopwords for text filtering
from nltk.tokenize import word_tokenize  # Importing word_tokenize function for tokenization
from nltk.stem.wordnet import WordNetLemmatizer  # Importing WordNetLemmatizer for lemmatization
from ast import literal_eval  # Importing literal_eval function for safe evaluation of strings
from langdetect import detect
from geopy.geocoders import Nominatim
import ast
import folium
from streamlit_folium import folium_static
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


# read data and process lat long
df = pd.read_csv('../data/accomodation_data_final.csv')
# df['lat/long'] = df['lat/long'].apply(eval)
# df[['Latitude', 'Longitude']] = pd.DataFrame(df['lat/long'].tolist(), columns=['Latitude', 'Longitude'])

# main header
st.title("Accommodation Recommendation")

# select state, description and top facility 
states = df['region_code'].unique()
selected_state = st.selectbox('Select A State You Wish to Visit', states) #dropdown box to select states
# filtered_df = df[df['region'] == selected_state]

brief_desc = st.text_area("What are you looking for?", placeholder="eg. Going for a honeymoon trip and looking for a place near Disneyland")
# st.write("Hotel Requrements: ", brief_desc)
facility_wanted = st.text_input("What facilities do you prioritise?", placeholder="eg. Non-smoking room, swimming pool, family room etc.")

st.sidebar.title('User Ratings')
user_ratings = []
for category in ['Location', 'Service', 'Cleanliness', 'Value', 'Facilities']:
    rating = st.sidebar.slider(f'{category} Rating', 1, 10, 5)
    user_ratings.append(rating)

## RECOMMENDER 1

def recommend_hotel(location, description, popular_facilities):
    df['description'] = df['description'].str.lower()
    df['region_code'] = df['region_code'].str.lower()
    description = description.lower()
    word_tokenize(description)
    stop_words = set(stopwords.words('english'))
    lemm = WordNetLemmatizer()
    filtered = {word for word in word_tokenize(description) if word not in stop_words}
    filtered_set = {lemm.lemmatize(fs) for fs in filtered}

    # Parse popular facilities
    popular_facilities = popular_facilities.split(', ')
    popular_facilities = {lemm.lemmatize(fs.lower()) for fs in popular_facilities}

    country = df[df['region_code'] == location.lower()]
    country = country.reset_index(drop=True)
    cos = []

    for i in range(country.shape[0]):
        temp_token = word_tokenize(country["description"][i])
        temp_set = {word for word in temp_token if word not in stop_words}
        temp2_set = {lemm.lemmatize(s) for s in temp_set}
        vector = temp2_set.intersection(filtered_set) | temp2_set.intersection(popular_facilities)
        cos.append(len(vector))

    country['similarity'] = cos
    country = country.sort_values(by='similarity', ascending=False).drop_duplicates(subset='hotel_name', keep='first')
    country.sort_values('overall_rating', ascending=False, inplace=True)
    country.reset_index(drop=True, inplace=True)
    
    # Filter out non-English hotel names
    country['lang'] = country['hotel_name'].apply(lambda x: detect(x))
    country = country[country['lang'] == 'en']

    # return country[["hotel_name", "lat/long", "description", "overall_rating", "popular_facilities", "Latitude", "Longitude"]].head()
    return country

recommended_hotels1 = recommend_hotel(selected_state, brief_desc, facility_wanted) # returns df of hotels recommended by recommender 1 above



# RECOMMENDER 2 

ratings = recommended_hotels1[['location', 'service', 'cleanliness', 'value', 'facilities']].values
# Normalise ratings using StandardScaler
scaler = StandardScaler()
ratings_normalized = scaler.fit_transform(ratings)
features = recommended_hotels1[['location', 'service', 'cleanliness', 'value', 'facilities', 'region_code']]
k = 50  
model = NearestNeighbors(n_neighbors=k, metric='cosine')
model.fit(ratings_normalized)

def get_top_recommendations(user_ratings):
    user_ratings_normalized = scaler.transform([user_ratings])
    distances, indices = model.kneighbors(user_ratings_normalized)
    recommended_indices = indices[0][1:]  # Exclude the first index, as it's the user's input
    recommended_hotels = recommended_hotels1.iloc[recommended_indices]
    return recommended_hotels[["hotel_name", "description", "overall_rating", "popular_facilities", "latitude", "longitude", "restaurant", "shopping_mall", "cafe", "bar", "supermarket", "park", "point_of_interest", "lodging", "museum"]].head() # return top 5 only




if st.button("Submit"):
    recommended_hotels = recommend_hotel(selected_state, brief_desc, facility_wanted)
    recommended_hotels_filtered = get_top_recommendations(user_ratings)
    
    center_latitude = recommended_hotels_filtered['latitude'].mean()
    center_longitude = recommended_hotels_filtered['longitude'].mean()
    m = folium.Map(location=[center_latitude, center_longitude], zoom_start=5)
    
    for index, row in recommended_hotels_filtered.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=folium.Popup(f"""
                               Accommodation Name: {row['hotel_name']} <br>
                               Rating: {row['overall_rating']}
                               """, max_width=len(f"Hotel Name: {row['hotel_name']}")*6)
        ).add_to(m)
    
    st.subheader("Recommended Accommodations on Map")
    folium_static(m)
    
    st.write("<h2 style='font-size:24px; font-weight:bold;'>Recommended Accommodations:</h2>", unsafe_allow_html=True)

    for index, row in recommended_hotels_filtered.iterrows():
        hotel_name = row['hotel_name']
        description = row['description']
        # overall_rating = row['overall_rating']
        popular_facilities = row['popular_facilities']
        
        
        st.markdown(f"**Accommodation Name:** {hotel_name}")
        st.markdown(f"**Description:** {description}")
        st.markdown(f"**Popular Facilities:** {popular_facilities}")
        counts = []
        for column in recommended_hotels_filtered.columns[6:]:  # include only nearby points of interest columns
            count = row[column]
            if pd.notna(count) and count != 0:  # Check for NaN and non-zero values
                counts.append(f"{int(count)} {column.replace('_', ' ').title()}(s)")
        if any(counts):  # Check if any non-NaN counts
            st.markdown(f"**There are the following facilities near you as well:** {', '.join(counts)}")
        # st.markdown(f"There are the following faacilities near you as well:" {})
        st.markdown("--------------------------------")  # Adding a separator between rows
        