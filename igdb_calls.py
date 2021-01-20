from igdb_utilities import get_data, open_json, to_json
import os
import sys
import inspect
from pprint import pprint
import random
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
    7: 'Season'
}

game_fields = ''' age_ratings.*, 
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

def game_info(input, name_or_id, approximate_match=True):
    try:  
        assert (name_or_id == 'name') or (name_or_id == 'id'), "Only name or id is accepted"
        if name_or_id == 'name':
            name_query = f'name ~ "{input}"' if not approximate_match else f'name ~ *"{input}"*'
        else:
            name_query = f'id = {input}' 
        query = f'fields {game_fields}; where {name_query};'
        data = get_data('games', query)
    except Exception as e:
        print('==================')
        print('Error in query:', e)
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
    else:
        return data

def lucky_game_info():
    try:
        query = f'fields {game_fields}; sort rating desc; limit 100; where rating != null & category=0;'
        data = get_data('games', query)
        idx = random.randint(0, len(data))
    except Exception as e:
        print('==================')
        print('Error in query:', e)
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
    else:
        return [data[idx]]

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

def involved_companies(game_id):
    try:
        query = f'fields involved_companies; where id = {game_id};'
        data = get_data('games', query)
        developers, publishers = {}, {}
        company_ids = ','.join([str(id) for id in data[0]['involved_companies']])
        sub_query = f'fields company.name, developer, publisher; where id = ({company_ids});'
        company_names = get_data('involved_companies', sub_query)
        for sub_dict in company_names:
            if sub_dict['developer']:
                developers[sub_dict['company']['id']] = sub_dict['company']['name']
            if sub_dict['publisher']:
                publishers[sub_dict['company']['id']] = sub_dict['company']['name']
    except Exception as e:
        print('==================')
        print('Error in query:', e)
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
    else:
        return developers, publishers    

def company_info(input, name_or_id, approximate_match=True):
    fields = ''' description,
        developed.name,
        name,
        parent.name,
        published.name,
        websites.url
    '''
    try:
        assert (name_or_id == 'name') or (name_or_id == 'id'), "Only name or id is accepted"
        if name_or_id == 'name':
            name_query = f'name ~ "{input}"' if not approximate_match else f'name ~ *"{input}"*'
        else:
            name_query = f'id = {input}'
        query = f'fields {fields}; where {name_query};'
        data = get_data('companies', query)
    except Exception as e:
        print('==================')
        print('Error in query:', e)
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
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

def prompt_multiple_results(info)->dict:
    results = {}
    if isinstance(info, list):
        if len(info) > 1:
            for title in info:
                results[title['name']] = title['id']
    return results

def get_image_url(id, endpoint='games', img_type='cover'):
    try:
        query = f'fields {img_type}.url; where id = {id};'
        data = get_data(endpoint, query)
        url = 'https:' + data[0][img_type]['url']
    except Exception as e:
        print('==================')
        print('Error in query:', e)
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
    else:
        return url

def company_games(company):
    try:
        company_query = f'fields name, published, developed; where id = {company};'
        companies = get_data('companies', company_query)
        game_ids = []
        if 'developed' in companies[0].keys():
            game_ids += companies[0]['developed']
        if 'published' in companies[0].keys():
            game_ids += companies[0]['published']
        game_ids = tuple(set(game_ids))
    
        game_query = f'fields name; sort rating desc; where id={game_ids} & category=0 & rating != null;'
        game_data = get_data('games', game_query)
    
        games = []
        for element in game_data:
            games.append(element['name'])

    except Exception as e:
        print('==================')
        print('Error in query:', e)
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
    else:
        return games

def top_rated():
    try:
        query = f'fields {game_fields};sort rating desc; where rating != null;'
        data = get_data('games', query)
    except Exception as e:
        print('==================')
        print('Error in query:', e)
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
    else:
        return data

def multiquery(endpoint:str, result_name:str, query:str):
    endpoint_result = f'query {endpoint} "{result_name}"'
    query = '' if not query else query
    multiquery = endpoint_result + ' {' + query + '};'
    data = get_data('multiquery', multiquery)
    return data

if __name__ == '__main__':
    #data = involved_companies(game_id='358')
    #print(data)
    data = company_games(company='421')
    pprint(data)
    


