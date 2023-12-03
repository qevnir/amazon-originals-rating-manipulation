import requests
from bs4 import BeautifulSoup
import time
import csv

headers = {
    'User-Agent': 'Your_User_Agent_String',
}
base_url = "https://www.metacritic.com"
search_url = base_url + "/browse/tv/all/all/all-time/userscore/?releaseYearMin=2000&releaseYearMax=2023&page={}"
SLEEP = 0.5

def extract_values(html):

    score_container = html.find(class_="c-productHero_score-container u-flexbox u-flexbox-column g-bg-white")
    if score_container:

        text_uppercase = score_container.find(class_="u-text-uppercase")
        text_uppercase = text_uppercase.get_text(strip=True)
        release_year = text_uppercase.split(',')[-1]
        if release_year == None:
            return  title_text, None, None,  None
        
        title_text = score_container.find(class_="c-productHero_title g-inner-spacing-bottom-medium g-outer-spacing-top-medium u-grid").div.get_text(strip=True)
        ratings_element = score_container.find('span', text=lambda t: t and "Based on" in t and "User Ratings" in t)
        if ratings_element == None:
            return title_text, None, release_year, None
        ratings_count_text = ratings_element.get_text(strip=True)
        ratings_count = ''.join(filter(str.isdigit, ratings_count_text.split("Based on")[-1]))


        review_value = score_container.find(class_="c-siteReviewScore_user")
        if review_value == None:
            return  title_text, None, release_year,  ratings_count
        review_value = review_value.span.get_text(strip=True)

        
        return title_text, review_value,  release_year, ratings_count
    else:
        return None, None, None, None


def scrape_website(output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'user_rating', 'rating_count', 'release']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        page_number = 84
        while True:  
            url = search_url.format(page_number)
            response = requests.get(url, headers=headers)
            time.sleep(SLEEP)
            if response.status_code != 200:
                break  # Break loop if page is not accessible

            
            html = BeautifulSoup(response.content, "html.parser")
            listings = html.find_all(class_="c-productListings")[0]
            extracted_data = []
            grid_elements = listings.find_all(class_="c-productListings_grid")

            # Some container of which there are usually (always?) two
            for grid_element in grid_elements:

                # Iterate each show 
                product_cards = grid_element.find_all(class_="c-finderProductCard")
                for card in product_cards:

                    # Retrieve link to show and request html from show page
                    product_link = card.find('a')['href']                    
                    product_response = requests.get(base_url + product_link, headers=headers)
                    print(product_link)
                    print(product_response.status_code)
                    time.sleep(SLEEP)
                    if product_response.status_code == 200:
                        # Process  html
                        html = BeautifulSoup(product_response.content, "html.parser")
                        title, rating, release, rating_count  = extract_values(html)
                        extracted_data.append({
                            'id':   product_link,
                            'title': title,
                            'user_rating': rating,
                            'rating_count': rating_count,
                            'release': release

                        })
                    else:
                        extracted_data.append({
                            'id':   product_link,
                            'title': None,
                            'user_rating': None,
                            'rating_count': None,
                            'release': None
                        })
                        
            page_number += 1  
            print("Page ", page_number)

            # Write to file after each page
            for data in extracted_data:
                writer.writerow(data)
            
scrape_website("metacritic_shows3.csv")

