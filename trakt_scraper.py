import requests
from bs4 import BeautifulSoup
import csv
import time
SLEEP = 0.1

base_url = "https://trakt.tv"

# Function to extract show data
def extract_show_data(html):
    time.sleep(SLEEP)

    soup = BeautifulSoup(html, 'html.parser')
    rating_value = soup.find(itemprop='ratingValue')
    rating_count = soup.find(itemprop='ratingCount')
    if rating_value != None and rating_count != None:
        rating = rating_value['content']
        votes = rating_count['content']
        return  rating, votes
    return None, None

# Load the CSV file and extract 'tconst' values into a list
tconst_list = []
with open('data/imdb_data.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        tconst_list.append(row['tconst'])

# Iterate through the tconst list
with open('trackt_data.csv', 'w', newline='') as csvfile:
    fieldnames = ['tconst', 'Rating', 'Votes']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    data_list = []
    count = 0
    for i, tconst in enumerate(tconst_list):
        url = base_url +  f"/search/imdb?query={tconst}"
        print(i, "{:.2%}".format(i / len(tconst_list)), tconst, url)
        time.sleep(SLEEP)
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            frame_imdb = soup.find(class_='frame imdb')
            if frame_imdb:
                grid_items = soup.find_all(class_='grid-item', attrs={'data-type': 'show'})
                for item in grid_items:
                    show_url = base_url + item['data-url']
                    response = requests.get(show_url)
                    rating, votes = extract_show_data(response.content)
                    if rating != None and votes != None:
                        data_list.append({'tconst': tconst, 'Rating': rating, 'Votes': votes})
            else:
                rating, votes = extract_show_data(response.content)
                data_list.append({'tconst': tconst, 'Rating': rating, 'Votes': votes})
                
        if i % 100 == 0:
            for data in data_list:
                writer.writerow(data)
            data_list = []

