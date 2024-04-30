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

def print_elements(elements):
    print("Start print_elements")
    if elements:
        count = 1
        for element in elements:
            print("-----")
            print(f"Counter: {count}")
            print("Tag Name:", element.tag_name)
            print("Attributes:", element.get_attribute("outerHTML"))
            print("-----")
            count+=1
    else:
        print("No elements found.")
    print("End print_elements")

def reject_claim_coupon(): # Not in use
    print("Start reject_claim_coupon")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="ab-message-buttons"]')))
    reject = driver.find_elements(By.CLASS_NAME, 'ab-message-button')
    #print_elements(reject)
    reject[1].click()
    print("End reject_claim_coupon")

def scroll_to_bottom():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # Wait for a short time to let new listings load
    time.sleep(3)

    # Scroll down repeatedly until no more new listings are loaded
    prev_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to the bottom
        scroll_to_bottom()
        # Wait for a short time to let new listings load
        time.sleep(3)
        # Check if scrolling reached the bottom
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == prev_height:
            break
        prev_height = new_height
    print("Done scrolling.")

def get_links(driver, url):
    driver.get(url)

    # Delay for page to load
    time.sleep(5)
    # May need to include delay for popup to automatically disappear upon url load

    # 15s delay for you to manually scroll till the listings are populated
    time.sleep(10) # Debug: Set to 1 for testing purposes
    print("End scroll.")

    # Retrieving Hotel list container
    hotel_list_container = driver.find_elements(By.CLASS_NAME, 'hotel-list-container')
    print(f"Total OL Count: {len(hotel_list_container)}")

    # Hotel listings are split into 2 ordered lists, sometimes more
    # Populate links to each hotel in a list
    hotel_links = []
    ol_count = 1
    for ol in hotel_list_container:
        hotel_listings = ol.find_elements(By.TAG_NAME, 'li')
        print(f"OL Number: {ol_count} - LI Count: {len(hotel_listings)}")

        # Iterate through each <li> element
        for item in hotel_listings:
            # Check if the element is displayed
            if item.value_of_css_property('display') != 'none':
                # If the element is displayed, add the link into list
                div_element = item.find_element(By.TAG_NAME, 'div')
                # Some items have divs that do not contain the hotel link.
                try:
                    #a_element = div_element.find_element(By.TAG_NAME, 'a')
                    a_element = div_element.find_element(By.CSS_SELECTOR, 'a[class="PropertyCard__Link"]')
                    #a_element = div_element.find_element(By.CSS_SELECTOR, 'a[data-element-name="property-card-content"]')
                    hotel_links.append(a_element.get_attribute('href'))
                except Exception as e:
                    continue

            # Waiting for <a> to be available:
            # a_element = WebDriverWait(div_element, 10).until(
            #     EC.presence_of_element_located((By.TAG_NAME, "a"))
            # )
            # hotel_links.append(a_element.get_attribute('href'))

    ol_count += 1

    # Checking links
    print(f"Number of hotel links: {len(hotel_links)}")
    # for i in range(10):
    #     print(hotel_links[-i])
    #     print("*****************************************************")
    
    return hotel_links
    
# Extract data from a link
def extract_data(driver, hotel_link):
    driver.get(hotel_link)
    time.sleep(2)
    data = {}

    # Hotel Name
    try:
        hotel_name_object = driver.find_element(By.CSS_SELECTOR, 'p[data-selenium="hotel-header-name"]')
        hotel_name = hotel_name_object.text
        data['Hotel Name'] = hotel_name
    except Exception as e:
        print(f"Hotel Name Not Found: {e}")

    # Overall Rating
    try:
        overall_rating_object = driver.find_element(By.CSS_SELECTOR, 'span[class="sc-jrAGrp sc-kEjbxe fzPhrN ehWyCi"]')
        overall_rating = overall_rating_object.text
        data['Overall Rating'] = overall_rating
    except Exception as e:
        print(f"Overall Rating Not Found: {e}")

    # Number of Total Reviews
    try:
        rating_count_object = driver.find_element(By.CSS_SELECTOR, 'p[class="Typographystyled__TypographyStyled-sc-j18mtu-0 Hkrzy kite-js-Typography "]')
        rating_count = rating_count_object.text
        data['Rating Count'] = rating_count
    except Exception as e:
        print(f"Rating Count Not Found: {e}")

    # Description
    try:
        description_object = driver.find_element(By.CSS_SELECTOR, 'p[class="Typographystyled__TypographyStyled-sc-j18mtu-0 fHvoAu kite-js-Typography "]')
        description = description_object.text
        data['Description'] = description
    except Exception as e:
        print(f"Description Not Found: {e}")
    
    # List of facilities
    facilities_list = []
    try:
        amenities_div = driver.find_elements(By.CSS_SELECTOR, 'div[data-element-name="atf-top-amenities-item"]')

        for item in amenities_div:
            p_object = item.find_element(By.TAG_NAME, 'p')
            p = p_object.text
            facilities_list.append(p)

    except Exception as e:
        print(f"Amenities Not Found: {e}")
    
    data['Facilities'] = facilities_list

    # Individual Ratings
    individual_ratings = {}
    try:
        indv_ratings_big_div = driver.find_element(By.CSS_SELECTOR, 'div[class="Review-travelerGrade-Cell"]')
        indv_ratings_div = indv_ratings_big_div.find_elements(By.CSS_SELECTOR, 'div[class="Review-travelerGrade"]')

        for item in indv_ratings_div:
            # rating_type_object = item.find_element(By.CSS_SELECTOR, 'span[class="Review-travelerGradeCategory"]')
            # rating_type = rating_type_object.text
            # rating_grade_object = item.find_element(By.CSS_SELECTOR, 'span[class="Review-travelerGradeScore Review-travelerGradeScore--highlight"')
            # rating_grade = rating_grade_object.text
            span_list = item.find_elements(By.TAG_NAME, 'span')
            rating_type = span_list[0].text
            rating_grade = span_list[1].text

            individual_ratings[rating_type] = rating_grade
    
    except Exception as e:
        print(f"Individual Ratings Not Found: {e}")

    data['Individual Ratings'] = individual_ratings
    data['Hotel Link'] = hotel_link    

    # print(hotel_name)
    # print(overall_rating)
    # print(rating_count)
    # print(description)
    # print(f"Length of facilities list: {len(facilities_list)}")
    # for i in facilities_list:
    #     print(i)

    # print(f"Length of individual ratings: {len(individual_ratings)}")
    # for key, value in individual_ratings.items():
    #     print(f"Type: {key}. Rating: {value}")

    return data

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.maximize_window()

url = 'https://www.agoda.com/search?guid=1c7c8d2b-8b75-4a9c-bf73-3ce5b2015cdf&asq=NQVGXW6jsE3tbdY9S%2BqUCpufa9Vwpz6XltTHq4n%2B9gPt6Sc9VYM%2BOtJvOdzFsuZ%2FspFlcwxpCBbdwpIGZ%2B753Ae4VzN8hLmFbfNcmJEH3FDgBpKyIriGe%2FUlPXlqlVkwp3tJbQ2oGUSBUjLxUHQeSnSk%2FM8eVuQYqDHVLhv%2F6oNbgjjG%2BjAYafKUEcXnaxuN01BiymAwtKHel%2BahAqoeBEHb%2BKC2e3zym6tmyvlzCzM%3D&city=8683&tick=638481277007&locale=en-us&ckuid=31087302-d84c-4103-b9eb-89999e7c1ec1&prid=0&currency=SGD&correlationId=2afd7d50-3264-40da-8d89-294702a0b28c&analyticsSessionId=1994797111930746271&pageTypeId=103&realLanguageId=1&languageId=1&origin=SG&cid=1844104&userId=31087302-d84c-4103-b9eb-89999e7c1ec1&whitelabelid=1&loginLvl=0&storefrontId=3&currencyId=5&currencyCode=SGD&htmlLanguage=en-us&cultureInfoName=en-us&machineName=sg-pc-6g-acm-web-user-6dcb498589-sfcvt&trafficGroupId=1&sessionId=x54mxhxeo2qsiwwokw4hraz3&trafficSubGroupId=84&aid=130589&useFullPageLogin=true&cttp=4&isRealUser=true&mode=production&browserFamily=Chrome&cdnDomain=agoda.net&checkIn=2024-04-22&checkOut=2024-04-23&rooms=1&adults=2&children=0&priceCur=SGD&los=1&textToSearch=Dallas+%28TX%29&productType=-1&travellerType=1&familyMode=off&ds=Pb8mG2wThecJJAqc'

# Get hotel link
hotel_links = get_links(driver, url)

all_hotel_data = []
for link in hotel_links:
    hotel_data = extract_data(driver, link)
    all_hotel_data.append(hotel_data)

df = pd.DataFrame(all_hotel_data)

df.to_excel('Agoda_Scraped.xlsx', index=False)

# Delay for debug
print("-Delay for debug-")
time.sleep(0)
driver.quit()
