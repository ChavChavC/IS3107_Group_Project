from bs4 import BeautifulSoup
import pandas as pd
import requests
import concurrent.futures
from tqdm import tqdm
from uszipcode import SearchEngine
import geocoder
import us
import re
import warnings
warnings.filterwarnings("ignore")

def get_hotel_details(hotel):
    try:
        url = hotel
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # get hotel name
        hotel_name_element = soup.find('a', class_='fn')
        hotel_name = hotel_name_element.text.strip() if hotel_name_element else None

        # get description
        desc_element =  soup.find('p', class_='a53cbfa6de b3efd73f69')
        desc = desc_element.text.strip() if desc_element else None

        # get best/popular facilities
        facilities = soup.find_all('span', class_="a5a5a75131")[:4]
        result = list(map(lambda x: x.text.strip(), facilities))
        result = set(result)
        result = ", ".join(result)

        # get overall rating (value)
        overall_rating_element = soup.find('div', class_='a3b8729ab1 d86cee9b25')
        overall_rating = float(overall_rating_element.contents[0].strip()) if overall_rating_element else None

        # get number of reviews
        num_reviews_element = soup.find('span', class_='a3b8729ab1 f45d8e4c32 d935416c47')
        num_reviews = int(num_reviews_element.contents[2].strip().split(' ')[0].replace(',', '')) if num_reviews_element else None

        # get address -> state -> state code + lat/long
        address_element = soup.find('span', class_='hp_address_subtitle js-hp_address_subtitle jq_tooltip')
        address = address_element.text.strip() if address_element else None
        if address:
            g = geocoder.arcgis(address)
            if g.ok:
                lat_long = g.latlng
            else:
                lat_long =  None
            regex = r'\b\d{5}\b'
            matches = re.findall(regex, address)
            zip_code = matches[0]
            search = SearchEngine()
            zcode = search.by_zipcode(zip_code)
            state_code = zcode.state
            state_name = us.states.lookup(state_code).name
        else:
            state_code = None
            state_name = None
            lat_long = None


        if overall_rating is None:
            rated = None

        # get individual ratings
        rating_div = soup.find_all('div', {'data-testid': 'review-subscore'})
        staff = get_rating(rating_div, 0)
        facilities = get_rating(rating_div, 1)
        cleanliness = get_rating(rating_div, 2)
        # comfort = get_rating(rating_div, 3)
        value_for_money = get_rating(rating_div, 4)
        location = get_rating(rating_div, 5)
        # free_wifi = get_rating(rating_div, 6)
        # print(hotel_name, overall_rating, rated, num_reviews, staff, facilities, cleanliness, comfort, value_for_money, location, free_wifi)
        return [hotel_name, lat_long, desc, result, overall_rating, num_reviews, state_name, state_code, cleanliness, staff, location, facilities, value_for_money]
    except Exception as e:
        print(e)
        
def get_rating(rating_div, index):
    if rating_div and len(rating_div) > index:
        rating_element = rating_div[index].find('div', class_='ccb65902b2 efcd70b4c4')
        return float(rating_element.text.strip()) if rating_element else None
    else:
        return None

# def process_hotels(hotels_list):
#     data = []
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         hotel_results = {executor.submit(get_hotel_details, hotel): hotel for hotel in hotels_list}
#         for future in concurrent.futures.as_completed(hotel_results):
#             hotel = hotel_results[future]
#             try:
#                 result = future.result()
#                 if result is not None:  
#                     data.append(result)
#                 else:
#                     print(f'No information found for hotel: {hotel}')
#             except Exception as exc:
#                 print(f'Error processing {hotel}: {exc}')
#     return data
    
def process_hotels(hotels_list):
    data = []
    max_workers = 10 
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    # with concurrent.futures.ThreadPoolExecutor() as executor:
        hotel_results = {executor.submit(get_hotel_details, hotel): hotel for hotel in hotels_list}
        with tqdm(total=len(hotel_results)) as pbar:
            for future in concurrent.futures.as_completed(hotel_results):
                hotel = hotel_results[future]
                try:
                    result = future.result()
                    if result is not None:  # Check if result is not None
                        data.append(result)
                    else:
                        print(f'No information found for hotel: {hotel}')
                except Exception as exc:
                    print(f'Error processing {hotel}: {exc}')
                pbar.update(1)  # Update progress bar
    return data

def main():
    with open('USA.xml', 'r') as f:
        data = f.read()
    Bs_data = BeautifulSoup(data, "xml")
    hotels_list = [loc.text for loc in Bs_data.find_all('loc')]
    hotels_list = list(filter(lambda x: '/us/' in x, hotels_list)) # list of all  hotel links in the specified region
    hotels_list = [url.replace('es-mx', 'en-gb') for url in hotels_list]

    data_frame = pd.DataFrame(columns=['hotel_name', 'lat/long', 'description', 'popular_facilities', 'overall_rating', 'total_num_of_reviews', 'region', 'region_shortform', 'cleanliness', 'service', 'location', 'facilities', 'value'])

    hotel_data = process_hotels(hotels_list)
    for hotel in hotel_data:
        data_frame.loc[len(data_frame)] = hotel
    data_frame = data_frame.dropna()
    data_frame.to_csv('USA_hotels_updated.csv', index=None)

if __name__ == "__main__":
    main()
