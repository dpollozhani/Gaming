from igdb_utilities import get_data, open_json, to_json
import os
from pprint import pprint
from time import sleep
from datetime import datetime,timedelta
#import pandas as pd

rating_enum = {1: 'Three', 
    2: 'Seven',
    3: 'Twelve',
    4: 'Sixteen',
    5: 'Eighteen',
    6: 'RP',
    7: 'EC',
    8: 'E',
    9: 'E10',
    10: 'T',
    11: 'M',
    12: 'AO'
}

rating_category_enum = {1: 'ESRB', 2: 'PEGI'}

status_enum = {0: 'Released',
    2: 'Alpha',
    3: 'Beta',
    4: 'Early access',
    5: 'Offline',
    6: 'Cancelled',
    7: 'Rumored'
}

game_category_enum = {0: 'Main game',
    1: 'Dlc addon',
    2: 'Expansion',
    3: 'Bundle',
    4: 'Standalone expansion',
    5: 'Mod',
    6: 'Episode',
    7: 'Season'}

def multiquery(endpoint:str, result_name:str, query:str):
    endpoint_result = f'query {endpoint} "{result_name}"'
    query = '' if not query else query
    multiquery = endpoint_result + ' {' + query + '};'
    data = get_data('multiquery', multiquery)
    return data

def game_info(name:str, approximate_match=True):
    fields = ''' age_ratings.*, 
        aggregated_rating,
        bundles.name,
        category,
        collection.name,
        dlcs.name,
        expansions.name,
        franchise.name,
        game_engines.name,
        game_modes.name,
        genres.name,
        keywords.name,
        name,
        parent_game.name,
        platforms.name,
        player_perspectives.name,
        release_dates.human,
        similar_games.name,
        status,
        summary,
        themes.name,
        total_rating,
        url
    '''
    try:
        name_query = f'~ "{name}"' if not approximate_match else f'~ *"{name}"*'
        query = f'fields {fields}; where name {name_query};'
        data = get_data('games', query)
    except Exception as e:
        print('Check the query:', e)
    else:
        return data

def clean_game_info(info):
    clean_info = {}
    for key, value in info.items():
        temp_value = []
        if isinstance(value, list):
            for sub_dict in value:
                if key == 'age_ratings':
                    temp_value.append(rating_category_enum[sub_dict['category']] + ' ' + rating_enum[sub_dict['rating']])
                elif 'name' in sub_dict.keys():
                    temp_value.append(sub_dict['name'])
                elif 'human' in sub_dict.keys():
                    temp_value.append(sub_dict['human'])
            clean_info[key] = '; '.join(sorted(list(set(temp_value))))
        elif isinstance(value, dict):
            if 'name' in value.keys():
                clean_info[key] = value['name']
        elif key == 'category':
            clean_info[key] = game_category_enum[value]
        elif key == 'url':
            clean_info[key] = f'<a target="_blank" href="{value}">IGDB page</a>'
        else:
            clean_info[key] = value
    
    return clean_info

def company_info(name:str, approximate_match=True):
    fields = ''' description,
        developed.name,
        name,
        parent.name,
        published.name,
        websites.url
    '''
    try:
        name_query = f'~ "{name}"' if not approximate_match else f'~ "{name}"*'
        query = f'fields {fields}; where name {name_query};'
        data = get_data('companies', query)
    except Exception as e:
        print('Check the query:', e)
    else:
        return data

def clean_company_info(info):
    clean_info = {}
    for key, value in info.items():
        temp_value = []
        if isinstance(value, list):
            for sub_dict in value:
                if 'name' in sub_dict.keys():
                    temp_value.append(sub_dict['name'])
                elif 'url' in sub_dict.keys():
                    temp_value.append(f'<a target="_blank" href="{sub_dict["url"]}">Company page</a>')
            clean_info[key] = '; '.join(sorted(list(set(temp_value))))
        elif isinstance(value, dict):
            if 'name' in value.keys():
                clean_info[key] = value['name']
        else:
            clean_info[key] = value
    return clean_info

def platform_info(name:str):
    pass

def clean_platform_info(info):
    pass

def prompt_multiple_results(info):
    text = ''
    if isinstance(info, list):
        if len(info) > 1:
            text = '<p style="font-size:13px;font-style:oblique;">Several matches were found:</p>'
            for title in info:
                title_name = title['name']
                text += f'<ul style="font-size:12px;">{title_name}</ul>'
    return text

def get_image_url(id, endpoint='games', img_type='cover'):
    try:
        query = f'fields {img_type}.url; where id = {id};'
        data = get_data(endpoint, query)
        url = 'https:' + data[0][img_type]['url']
    except Exception as e:
        print('Cover not available:', e)
        url = ''
    else:
        return url

def company_game_ratings(company:str, cache_file=None):
    company_query = f'fields name, published; where name ~ "{company}";'
    companies = get_data('companies', company_query)
    
    assert isinstance(companies, list) and len(companies) == 1, 'Too many companies where found with that name, please specify'
    
    if any(cache_file) and os.path.exists(cache_file):
        cache = set([d['id'] for d in open_json(cache_file)])
        print('Cache:', cache)
    else:
        cache = []

    games = []
    try:
        print('Fetching games. Enjoy a cup of coffee in the meantime...')
        start_time = datetime.now()
        for game_id in companies[0]['published']:
            if game_id not in cache:
                if datetime.now() - start_time < timedelta(0,60):
                    game_query = f'fields name, aggregated_rating, first_release_date; where id={game_id} & category=0;'
                    game_data = get_data('games', game_query)
                    if isinstance(game_data, list) and len(game_data) == 1:
                        games.append(game_data[0])
        games = sorted(games, key = lambda i: i.get('aggregated_rating', -1), reverse=True)
    except Exception as e:
        print('Error encountered:', e)
    finally:
        return games

def latest_releases(platform_name:str):
    pass

        
if __name__ == '__main__':
    data = company_info('Nintendo', approximate_match=False)
    pprint(clean_company_info(data[0]))

    #print(datetime.fromtimestamp(765244800).strftime('%Y-%m-%d'))


