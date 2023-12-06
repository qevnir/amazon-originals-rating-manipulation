from bs4 import BeautifulSoup
import csv


def extract_year_from_text(text):
    parts = text.split(',')
    if len(parts) > 1:
        year_part = parts[-1].strip() 
        if year_part.isdigit():  
            return int(year_part)
    return None

def extract_info(html_file, output_file):

    # Read html file
    with open(html_file, 'r', encoding='utf-8') as file:
        html = file.read()

    soup = BeautifulSoup(html, 'html.parser')
    extracted_data = []
    card_elements = soup.find_all('div', class_='card style_1')
    
    for card in card_elements:
        # Extract info from each card 
        a_href = card.find('a').get('href')
        percent = float(card.find('div', {'data-percent': True}).get('data-percent'))
        percent = round(percent, 2)
        h2_text = card.find('h2').text
        p_text = card.find('h2').find_next('p').text
        release_year = extract_year_from_text(p_text)

        # Append data to dict
        extracted_data.append({
            'id': a_href.split('/')[-1], 
            'title': h2_text,
            'rating': percent,
            'release': release_year if release_year is not None else None 
        })
    
    # Write file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'rating', 'release']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in extracted_data:
            writer.writerow(data)

input_html_file = "html/moviedb.html"
output_csv_file =  "data/moviedb_data.csv"

extract_info(input_html_file, output_csv_file)
