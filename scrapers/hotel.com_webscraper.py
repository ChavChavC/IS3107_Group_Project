import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

#lost_data = 0

def show_more():
    while True:
        time.sleep(1)
        try:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Find and click the "Show more" button
            show_more_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-stid="show-more-results"]'))
            )
            show_more_button.click()

        except Exception as e:
            # If the button is not found, break out of the loop
            print(f"Exception: {e} No more results.")
            break

# def close_cookie():
#     try:
#         # Wait for the cookie popup to appear
#         cookie_popup = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "onetrust-banner-sdk")))

#         # Find the button to accept the cookies
#         accept_button = cookie_popup.find_element(By.ID, "onetrust-accept-btn-handler")
#         accept_button.click()
        
#         print("Cookie popup closed.")
        
#     except NoSuchElementException:
#         print("Cookie popup not found.")
#     except Exception as e:
#         print(f"Error while handling cookie popup: {e}")


def extract_data():

    data_list = []

    hotel_name = driver.find_element(By.TAG_NAME, 'h1').text

    #See all reviews
    all_reviews = driver.find_element(By.CSS_SELECTOR, 'button[data-stid="reviews-link"]')
    all_reviews.click()
    time.sleep(4)

    # Guest Reviews tab open
    app_layer = driver.find_element(By.ID, 'app-layer-reviews')
    section = app_layer.find_element(By.TAG_NAME, 'section')
    div_section = section.find_element(By.CSS_SELECTOR, '.uitk-sheet-content.uitk-sheet-content-padded.uitk-sheet-content-extra-large')
    property_reviews_summary = div_section.find_element(By.CSS_SELECTOR, 'div[data-stid="property-reviews-summary"]')

    # Remove AI new div if found: 'div[data-stid="product-summarized-reviews"]'
    try:
        div_to_remove = property_reviews_summary.find_element(By.CSS_SELECTOR, 'div[data-stid="product-summarized-reviews"]')
        div_to_remove.parent.execute_script("arguments[0].remove()", div_to_remove)
    except NoSuchElementException:
        print("cant find extra div!")

    # Overall Rating Text
    overall_rating = property_reviews_summary.find_element(By.TAG_NAME, 'span')
    overall_rating_score = overall_rating.text

    # Finding Individual Rating Div

    # test = property_reviews_summary.find_elements(By.XPATH, './/*')

    # count = 0
    # for element in test:
    #     print("-----")
    #     print(f"Counter: {count}")
    #     print("Tag Name:", element.tag_name)
    #     print("Attributes:", element.get_attribute("outerHTML"))
    #     print("-----")
    #     count+=1

    # Total Reviews
    indv_review_list = property_reviews_summary.find_elements(By.XPATH, './/*')
    total_reviews = indv_review_list[7].text

    indv_review_portion = indv_review_list[16]
    indv_review_data = indv_review_portion.find_elements(By.XPATH, './/*')

    # count = 0
    # for element in indv_review_data:
    #     print("-----")
    #     print(f"Counter: {count}")
    #     print("Tag Name:", element.tag_name)
    #     print("Attributes:", element.get_attribute("outerHTML"))
    #     print("-----")
    #     count+=1

    #cleanliness = indv_review_data[3].text
    cleanliness_score = indv_review_data[4].text
    staff_and_service_score = indv_review_data[12].text
    amenities_score = indv_review_data[20].text
    property_conditions_and_facilities_score = indv_review_data[28].text
    eco_friendliness_score = indv_review_data[36].text

    print(hotel_name)
    print(overall_rating_score)
    print(total_reviews)
    print(cleanliness_score)
    print(staff_and_service_score)
    print(amenities_score)
    print(property_conditions_and_facilities_score)
    print(eco_friendliness_score)

    data_list.append(hotel_name)
    data_list.append(overall_rating_score)
    data_list.append(total_reviews)
    data_list.append(cleanliness_score)
    data_list.append(staff_and_service_score)
    data_list.append(amenities_score)
    data_list.append(property_conditions_and_facilities_score)
    data_list.append(eco_friendliness_score)

    return data_list

def click_back():
    # Switch to the newly opened tab
    time.sleep(4)
    driver.switch_to.window(driver.window_handles[1])

    # Extract here
    try:
        temp_list = extract_data()
        data.append(temp_list)
    except Exception as e:
        #lost_data += 1
        print(f"Data not available.")

    # Close the new tab when done
    driver.close()

    # Switch back to the original tab
    driver.switch_to.window(driver.window_handles[0])

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

try:
    hotel_dict = {
        "newyork": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=New%20York%2C%20New%20York%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=40.712843%2C-74.005966&mapBounds=&pwaDialog=&regionId=2621&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "texas": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Houston%2C%20Texas%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=29.75869%2C-95.36588&mapBounds=&pwaDialog=&regionId=1503&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "illinois":"https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Illinois%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=40.12399816771237%2C-89.1484976816067&mapBounds=&pwaDialog=&regionId=215&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "pennsylvania":"https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Pennsylvania%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=40.266311%2C-76.886112&mapBounds=&pwaDialog=&regionId=240&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "arizona": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Arizona%2C+United+States+of+America&endDate=2024-03-25&latLong=33.448437%2C-112.074141&mapBounds=&pwaDialog=&regionId=204&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "florida": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Orlando%2C+Florida%2C+United+States+of+America&endDate=2024-03-25&latLong=28.54129%2C-81.37904&mapBounds=&pwaDialog=&regionId=2693&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "indiana": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Indianapolis%2C%20Indiana%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=39.768402%2C-86.158066&mapBounds=&pwaDialog=&regionId=1598&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "ohio": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Cleveland%2C%20Ohio%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=41.50022%2C-81.69357&mapBounds=&pwaDialog=&regionId=859&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "michigan": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Michigan%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=44.314846%2C-85.602364&mapBounds=&pwaDialog=&regionId=224&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "north_carolina": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=North%20Carolina%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=35.719758%2C-79.453125&mapBounds=&pwaDialog=&regionId=235&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "tennessee": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Tennessee%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=36.162277%2C-86.774298&mapBounds=&pwaDialog=&regionId=244&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "washington": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=Downtown%20Washington%20D.C.%2C%20Washington%2C%20District%20of%20Columbia%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=38.902076357314904%2C-77.03039826105964&mapBounds=&pwaDialog=&regionId=800144&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent=",
        "district_of_columbia": "https://sg.hotels.com/Hotel-Search?adults=2&allowPreAppliedFilters=true&children=&destination=District%20of%20Columbia%2C%20United%20States%20of%20America&endDate=2024-03-25&latLong=38.907238%2C-77.036524&mapBounds=&pwaDialog=&regionId=210&rooms=1&semdtl=&sort=RECOMMENDED&startDate=2024-03-24&theme=&useRewards=false&userIntent="
        
        }
    
    for key,value in hotel_dict.items():
        driver.get(value)

        time.sleep(2)

        data = []

        show_more()

        #hotels = driver.find_elements(By.CLASS_NAME, 'uitk-card-link')
        hotels = driver.find_elements(By.CSS_SELECTOR, 'a[data-stid="open-hotel-information"]')
        print(len(hotels))

        # close cookie div at start
        try:
            cookies_remove = driver.find_element(By.ID, 'onetrust-consent-sdk')
            cookies_remove.parent.execute_script("arguments[0].remove()", cookies_remove)
            print('Cookie div removed')
        except NoSuchElementException:
            print("Cant find cookie!")

        for i in range(len(hotels)): #change to len(hotels)
            try:
                print(f"{i}/{len(hotels)}")
                #time.sleep(5000)
                # close cookie
                try:
                    cookies_remove = driver.find_element(By.ID, 'onetrust-consent-sdk')
                    cookies_remove.parent.execute_script("arguments[0].remove()", cookies_remove)
                    print('Cookie div removed')
                except Exception:
                    print("Cant find cookie [loop]!")

                hotels[i].click()
                click_back()
                time.sleep(1)
                print('---')
            except Exception as ex:
                #lost_data += 1
                print(f"Exception for hotel {i+1}: {ex}")
                time.sleep(5000)
                continue

        columns = ['Hotel', 'Overall Rating', 'Total Reviews', 'Cleanliness', 'Staff and Service', 'Amenities', 'Property Conditions and Facilities', 'Eco-Friendliness']
        df = pd.DataFrame(data, columns=columns)
        df_no_duplicates = df.drop_duplicates()
        filename = f'hotel_dot_com_review_data_{key}.csv'
        df_no_duplicates.to_csv(filename, index=False)
        print(f"CSV file saved for {key}")

except Exception as e:
    print(f"Exception during execution: {e}")

finally:
    time.sleep(5)
    driver.quit()
    # columns = ['Hotel', 'Overall Rating', 'Total Reviews', 'Cleanliness', 'Staff and Service', 'Amenities', 'Property Conditions and Facilities', 'Eco-Friendliness']
    # df = pd.DataFrame(data, columns=columns)
    # df_no_duplicates = df.drop_duplicates()
    # filename = f'hotel_dot_com_review_data_{key}.csv'
    # df_no_duplicates.to_csv(filename, index=False)
    #print(f"Number of listings lost due to error: {lost_data}/{len(hotels)}")