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

multiplayer_fields = '''
    platform.name,
    campaigncoop,
    lancoop,
    offlinecoop,
    offlinecoopmax,
    offlinemax,
    onlinecoop,
    onlinecoopmax,
    onlinemax,
    splitscreen 
    '''
    
multiplayer_field_map = {
    'campaigncoop': 'Campaign co-op',
    'lancoop': 'LAN co-op',
    'offlinecoop': 'Offline co-op',
    'offlinecoopmax': 'Offline co-op max players',
    'offlinemax': 'Offline max players',
    'onlinecoop': 'Online co-op',
    'onlinecoopmax': 'Online co-op max players',
    'onlinemax': 'Online max players',
    'splitscreen': 'Splitscreen'
    }

company_fields = ''' description,
    developed.name,
    name,
    parent.name,
    published.name,
    websites.url
    '''

def prompt_multiple_results(info):
    results = {}
    if isinstance(info, list):
        if len(info) > 1:
            for title in info:
                results[title['name']] = title['id']
    return results

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