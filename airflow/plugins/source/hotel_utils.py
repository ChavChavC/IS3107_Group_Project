import requests
import pandas as pd
import ast

def get_hotel_info(api_key, hotel_name):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={hotel_name}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if 'results' in data and data['results']:
        first_result = data['results'][0]
        hotel_info = {
            'Original Hotel Name': hotel_name,
            'Hotel Name': first_result['name'],
            'Geometry': first_result['geometry']['location'],
            'Address': first_result['formatted_address'],
            'Rating': first_result.get('rating', 'N/A'),
            'Place ID': first_result['place_id']
        }
        return hotel_info
    else:
        print(f"No results found for {hotel_name}.")
        return None

def count_nearby_places(api_key, location, radius=5000, types=None):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location['lat']},{location['lng']}&radius={radius}&key={api_key}"
    if types:
        url += f"&types={','.join(types)}"

    response = requests.get(url)
    data = response.json()

    type_counts = {place_type: 0 for place_type in types}

    if 'results' in data:
        for place in data['results']:
            place_types = place.get('types', [])
            for place_type in place_types:
                if place_type in type_counts:
                    type_counts[place_type] += 1

    return type_counts

def enrich_agoda_data(api_key, hotel_data):

    hotel_data = hotel_data.head(500)
    types = ['restaurant', 'shopping_mall', 'tourist_attraction', 'cafe', 'bar', 'supermarket', 'park', 'point_of_interest', 'lodging', 'museum']
    output_data = pd.DataFrame(columns=['Original Hotel Name', 'Hotel Name', 'Geometry', 'Address', 'Rating', 'Place ID'] + types)

    for hotel_name in hotel_data['hotel_name']:
        hotel_info = get_hotel_info(api_key, hotel_name)
        if hotel_info:
            location = hotel_info['Geometry']
            type_counts = count_nearby_places(api_key, location, types=types)
            hotel_info.update(type_counts)
            new_row = pd.DataFrame([hotel_info])
            new_row['Geometry'] = new_row['Geometry'].astype(str)
            new_row['lat/long'] = new_row['Geometry'].apply(lambda x: ast.literal_eval(x))
            new_row['latitude'] = new_row['lat/long'].apply(lambda x: x.get('lat'))
            new_row['longitude'] = new_row['lat/long'].apply(lambda x: x.get('lng'))
            new_row.drop(columns=['lat/long'], inplace=True)
            output_data = pd.concat([output_data, new_row], ignore_index = True)
        else:
            new_row = pd.DataFrame([{'Original Hotel Name': hotel_name, 'Hotel Name': 'No information found', 'Geometry': 'N/A', 'latitude': 'N/A', 'longitude': 'N/A', 'Address': 'N/A', 'Rating': 'N/A', 'Place ID': 'N/A'}])
            output_data = pd.concat([output_data, new_row], ignore_index = True)

    output_data.drop(columns=["Geometry"], inplace = True)
    
    return output_data

def enrich_booking_data(api_key, hotel_data):
    hotel_data = hotel_data.head(500)
    types = ['restaurant', 'shopping_mall', 'tourist_attraction', 'cafe', 'bar', 'supermarket', 'park', 'point_of_interest', 'lodging', 'museum']
    output_data = pd.DataFrame(columns=['Hotel Name', 'latitude', 'longitude'] + types)

    for index, row in hotel_data.iterrows():
        hotel_name = row['hotel_name']
        location = {"lat": row['latitude'], "lng": row['longitude']}
        type_counts = count_nearby_places(api_key, location, types=types)
        hotel_info = {'Hotel Name': row['hotel_name'], 'latitude': row['latitude'], 'longitude': row['longitude']}
        hotel_info.update(type_counts)
        new_row = pd.DataFrame([hotel_info])
        output_data = pd.concat([output_data, new_row], ignore_index = True)

    return output_data
    
