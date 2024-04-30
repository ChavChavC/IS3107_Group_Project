import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static

# Sample hotel data (replace with your actual data source)
data = {
    'Hotel_Name': ['Hotel A', 'Hotel B', 'Hotel C', 'Hotel D'],
    'Price': [100, 150, 200, 120],
    'Latitude': [37.7833, 37.7749, 37.7698, 37.7782],
    'Longitude': [-122.4167, -122.4194, -122.4064, -122.4056]
}
hotels_df = pd.DataFrame(data)

# User input section for location and price range
st.title("Hotel Recommendation System")
user_location = st.text_input("Enter your desired location:")
min_price = st.number_input("Minimum Price per night:", min_value=0)
max_price = st.number_input("Maximum Price per night:", min_value=min_price)

# Filter hotels based on user input
filtered_hotels = hotels_df[
    (hotels_df['Price'] >= min_price) & (hotels_df['Price'] <= max_price)
]

if user_location:
    # Placeholder for location filtering based on user input (replace with actual filtering logic)
    st.write("Location filtering logic to be implemented based on user input")
    # Assuming all hotels are relevant based on location for now
    filtered_hotels = filtered_hotels.copy()

# Display recommended hotels
st.subheader("Recommended Hotels")
if not filtered_hotels.empty:
    col1, col2 = st.columns(2)
    for index, row in filtered_hotels.iterrows():
        with col1:
            st.write(f"{row['Hotel_Name']}")
        with col2:
            st.write(f"Price: ${row['Price']} per night")
else:
    st.write("No hotels found based on your criteria.")

# Create interactive map
center_latitude = filtered_hotels['Latitude'].mean()
center_longitude = filtered_hotels['Longitude'].mean()

m = folium.Map(location=[center_latitude, center_longitude], zoom_start=13)

# Add markers for recommended hotels
for index, row in filtered_hotels.iterrows():
    folium.Marker(
        [row['Latitude'], row['Longitude']],
        popup=f"{row['Hotel_Name']}: ${row['Price']} per night",
        max_width = 300
    ).add_to(m)

# # Display recommended hotels (DataFrame)
# st.subheader("Recommended Hotels")
# st.write(filtered_hotels)  # Display DataFrame with hotel details

# Display the interactive map using st.map(m)
st.subheader("Recommended Hotels on Map")
folium_static(m)