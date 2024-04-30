import streamlit as st
import pandas as pd
import numpy as np

# Sample hotel data
hotel_data = {
    'Hotel': ['Hotel A', 'Hotel B', 'Hotel C', 'Hotel D', 'Hotel E'],
    'Location': ['Location A', 'Location B', 'Location A', 'Location C', 'Location B'],
    'StarRating': [3, 4, 5, 3, 4],
    'Price': [100, 150, 200, 120, 180]
}
df_hotels = pd.DataFrame(hotel_data)

# Streamlit app
st.title('Hotel Recommendation System')

# Sidebar inputs
budget = st.sidebar.slider('Budget', min_value=50, max_value=300, value=150, step=10)
location = st.sidebar.selectbox('Location', df_hotels['Location'].unique())
star_rating = st.sidebar.slider('Minimum Star Rating', min_value=1, max_value=5, value=3, step=1)

# Filter hotels based on inputs
filtered_hotels = df_hotels[(df_hotels['Price'] <= budget) & (df_hotels['Location'] == location) & (df_hotels['StarRating'] >= star_rating)]

# Display recommendations
if filtered_hotels.empty:
    st.write("No hotels found matching the criteria.")
else:
    st.write("Recommended Hotels:")
    st.table(filtered_hotels)