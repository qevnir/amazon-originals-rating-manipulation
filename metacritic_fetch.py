import requests
from bs4 import BeautifulSoup
import time
import csv
import pandas as pd
import os

headers = {
    'User-Agent': 'Your_User_Agent_String',
}
base_url = "https://www.metacritic.com"
search_url = "/browse/tv/all/all/all-time/userscore/?releaseYearMin=2000&releaseYearMax=2023&page={}"
SLEEP = 0.1


def extract_score(html, score_type):
    
    score_element = None
    if score_type.lower() == "metascore":
        score_element = html.find('span', string=lambda t: t and "Metascore" in t)
    elif score_type.lower() == "userscore":
        score_element = html.find('span', string=lambda t: t and "User Score" in t)
    if score_element:
        score_value = score_element.find_next(class_="c-siteReviewScore_medium").get_text(strip=True)
        num_reviews_element = score_element.find_next('span', class_="c-productScoreInfo_reviewsTotal")
        if num_reviews_element != None:
            num_reviews_text = num_reviews_element.get_text(strip=True)
            num_reviews = ''.join(filter(str.isdigit, num_reviews_text.split("Based on")[-1]))
            return score_value, num_reviews

    return None, None


def extract_title(html):
    title_text = html.find(class_="c-productHero_title g-inner-spacing-bottom-medium g-outer-spacing-top-medium u-grid").div.get_text(strip=True)
    return title_text

def extract_year(html):
    text_uppercase = html.find(class_="u-text-uppercase")
    text_uppercase = text_uppercase.get_text(strip=True)
    release_year = text_uppercase.split(',')[-1]
    return release_year

def extract_values(html):

    score_container = html.find(class_="c-productHero_score-container u-flexbox u-flexbox-column g-bg-white")
    if score_container:

        year = extract_year(score_container)
        title = extract_title(score_container)
        metascore, num_reviews = extract_score(score_container, 'metascore')
        rating_value, ratings_count = extract_score(score_container, 'userscore')
        
        return title, rating_value, year, ratings_count, metascore, num_reviews
    else:
        return None, None, None, None, None, None

def extract_product_cards(html):
    listings = html.find_all(class_="c-productListings")[0]
    grid_elements = listings.find_all(class_="c-productListings_grid")
    cards = []

    # Some container of which there are usually (always?) two
    for grid_element in grid_elements:
        product_cards = grid_element.find_all(class_="c-finderProductCard")
        cards = cards + product_cards

    return cards

def scrape_site(output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'user_rating', 'rating_count', 'metascore', 'review_count','release']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        page_number = 1
        while True:  
            url = base_url + search_url.format(page_number)
            response = requests.get(url, headers=headers)
            time.sleep(SLEEP)
            if response.status_code != 200:
                break  # Break loop if page is not accessible

            
            html = BeautifulSoup(response.content, "html.parser")
            product_cards = extract_product_cards(html)
            extracted_data = []

            # iterate through titles and extract data
            for card in product_cards:

                # Retrieve link to show and request html from show page
                product_link = card.find('a')['href']                    
                product_response = requests.get(base_url + product_link, headers=headers)
                print(product_link)
                print(product_response.status_code)
                time.sleep(SLEEP)
                                
                title = rating = rating_count = release =  metascore = review_count = None

                if product_response.status_code == 200:
                    html = BeautifulSoup(product_response.content, "html.parser")
                    title, rating, release, rating_count, metascore, review_count  = extract_values(html)

                extracted_data.append({
                    'id':   product_link,
                    'title': title,
                    'user_rating': rating,
                    'rating_count': rating_count,
                    'metascore': metascore,
                    'review_count': review_count,
                    'release': release    
                    })
                    
            page_number += 1  
            print("Page ", page_number)

            # Write to file after each page
            for data in extracted_data:
                writer.writerow(data)




output_file = "metacritic_tmp"
iterations = 4
files = []
for i in range(iterations):
    filename = output_file + str(i+1) + ".csv"
    scrape_site(filename)
    files.append(filename)
    None

combined_df = pd.concat((pd.read_csv(os.path.join('./', f)) for f in files), ignore_index=True)
combined_df = combined_df.drop_duplicates()

combined_df.to_csv('data/metacritic_data.csv', index=False)

# delete tmp files
for f in files:
        os.remove(f)

