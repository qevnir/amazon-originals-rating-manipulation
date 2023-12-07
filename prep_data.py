import pandas as pd
import re



# cleans metacritic data for parenthesis
def regex_filter(text):
    pattern = r'\((?:[a-z]{2}|\d{4})\)|marvel\'s\s*'  # Regex pattern to match two uppercase letters or four digits inside parentheses
    matches = re.findall(pattern, text)
    for match in matches:
        text = text.replace(match, '')  # Replace the matched pattern with an empty string
    return text.strip()


# prepare imdb data
# filter tv shows after 2000
df = pd.read_csv("data/imdb/title_basic.tsv", sep='\t')
filtered_df = df.loc[((df['titleType'] == 'tvSeries') |
                     (df['titleType'] == 'tvMiniSeries')) &
                     (df['isAdult'] == 0)
                    ]
filtered_df = filtered_df[filtered_df['startYear'].apply(lambda x: x.isdigit() and int(x) >= 2000)]

# filter regional to US and GB and merge
columns_to_load = ['titleId', 'language', 'region']
df = pd.read_csv('data/imdb/title_akas.tsv', sep='\t', usecols=columns_to_load)
df_en = df[(df['region'] == 'US') | (df['region'] == 'GB')]
merged_df = pd.merge(filtered_df, df_en, left_on='tconst', right_on='titleId')
merged_df = merged_df.drop(['region', 'language', 'titleId'], axis=1)
merged_df = merged_df.drop_duplicates()


# filter shows with more than 2000 ratings
df_ratings = pd.read_csv('data/imdb/title_ratings.tsv', sep='\t')
merged_df = pd.merge(merged_df, df_ratings)
imdb_df = merged_df[(merged_df['numVotes'] > 2000)]
imdb_df['startYear'] = imdb_df['startYear'].astype('int64')
# output filtered data
#imdb_df.to_csv('data/imdb_data.csv', index=False)



# Prepare metacritic data
metacritic_df = pd.read_csv("data/metacritic_data.csv")
metacritic_df = metacritic_df[metacritic_df['release'] >= 2000]


# Merge all datasets
imdb_df['_primaryTitle'] = imdb_df['primaryTitle'].str.lower()
imdb_df['_originalTitle'] = imdb_df['originalTitle'].str.lower()
imdb_df.rename(columns={'averageRating': 'imdb_rating', 'numVotes': 'imdb_numVotes'}, inplace=True)

metacritic_df['_title'] = metacritic_df['title'].str.lower()
metacritic_df.rename(columns={'user_rating': 'metacritic_rating', 'rating_count': 'metacritic_numVotes'}, inplace=True)
tmdb_df = pd.read_csv("data/tmdb_data.csv")
tmdb_df['_title'] = tmdb_df['title'].str.lower()
tmdb_df.rename(columns={'rating': 'tmdb_rating'}, inplace=True)


# clean titles for parenthesis and "Marvel" prefix from Marvel productions
metacritic_df['_title'] = metacritic_df['_title'].map(regex_filter)
tmdb_df['_title'] = tmdb_df['_title'].map(regex_filter)


# then merge TMDB data with IMDB data
merged_df = pd.merge(imdb_df, tmdb_df, left_on=['_primaryTitle', 'startYear'], right_on=['_title', 'release'], how='left', suffixes=('_imdb', '_tmdb_df'))
unmatched_tmdb_df = merged_df[merged_df['id'].isnull()].drop(columns=[col for col in merged_df.columns if '_imdb' in col])
tmdb_merged_df = merged_df.dropna()

print("Dataset shape after TMDB merge with IMDb set: ", tmdb_merged_df.shape)

# first merge Metacritic data with IMDB data
merged_df = pd.merge(imdb_df, metacritic_df, left_on=['_primaryTitle', 'startYear'], right_on=['_title', 'release'], how='left', suffixes=('_imdb', '_metacritic'))
metacritic_merged_df = merged_df.dropna()
print("Dataset shape after Metacritic merge with IMDb set: ", metacritic_merged_df.shape)





# finally load trakt dataset and merge all sets

trakt_df = pd.read_csv("data/trakt_data.csv")
trakt_df.rename(columns={'Rating': 'trakt_rating', 'Votes': 'trakt_numVotes'}, inplace=True)
merged_df = pd.merge(metacritic_merged_df, tmdb_merged_df, on='tconst')
merged_df = pd.merge(merged_df, trakt_df, on='tconst')
print(merged_df.columns)

merged_df.rename(columns={'title_y': 'title', 'startYear_x': 'startYear',
                               'imdb_rating_x': 'imdb_rating', 'imdb_numVotes_x': 'imdb_numVotes',
                               }, inplace=True)
merged_df_final = merged_df[['tconst','title','startYear', 'imdb_rating', 
                             'imdb_numVotes','tmdb_rating','trakt_rating',
                             'trakt_numVotes', 'metacritic_rating', 'metacritic_numVotes', 'metascore', 'review_count']]

# Remove duplicates caused by trakt data being inconsistent
merged_df_final = merged_df_final.loc[merged_df_final.groupby(['title', 'startYear'])['trakt_numVotes'].idxmax()]
merged_df_final = merged_df_final.drop_duplicates()

# Write to file
merged_df_final.to_csv('data/all_ratings_data.csv', index=False)
