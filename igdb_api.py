from igdb_authentication import get_token
from igdb.wrapper import IGDBWrapper
import igdb_utilities
import json
from ast import literal_eval
import requests
import random 

import os
import sys
import inspect

class IGBDAPI():

    def __init__(self, wrapper):
        assert isinstance(wrapper, IGDBWrapper), 'wrapper must be instance of class igbd.wrapper.IGBWrapper'
        self.wrapper = wrapper
    
    def query_endpoint(self, endpoint:str, query:str):
        
        byte_array = self.wrapper.api_request(
                    endpoint,
                    query 
                    )
        try:
            return json.loads(byte_array)
        except requests.exceptions.RequestException as e:
            print('Error in request:', e)
        except Exception as e:
            evaluation_error = True
        if evaluation_error:
            print('Response format is not json/cannot be evaluated, returning as byte array')
            return byte_array

    def multiquery(self, endpoint:str, result_name:str, query:str):
        
        endpoint_result = f'query {endpoint} "{result_name}"'
        query = '' if not query else query
        multiquery = endpoint_result + ' {' + query + '};'
        multiquery_result = self.query_endpoint('multiquery', multiquery)
        
        return multiquery_result

    def get_game_info(self, input, name_or_id='name', approximate_match=True):
        
        assert (name_or_id == 'name') or (name_or_id == 'id'), "Only name or id is accepted"
        
        fields = igdb_utilities.game_fields
        
        if name_or_id == 'name':
            if not approximate_match:
                query = f'fields {fields}; where name ~ "{input}";'
            else:
                query = f'search "{input}"; fields {fields};' 
        else:
            query = f'fields {igdb_utilities.game_fields}; where id = {input};'
        game_info = self.query_endpoint('games', query)

        return game_info

    def get_lucky_game_info(self, limit=1, **where_filters):
        query_appendix = []
        
        for name,value in where_filters.items():
            equality = '='
            if any(i in value for i in ['>=', '<=']):
                equality = value[:2]
                value = value[2:]
            elif any(i in value for i in ['<', '>']):
                equality = value[:1]
                value = value[1:]
            query_appendix.append(f'{name}{equality}{value}')
        if len(query_appendix) > 0:
            query_appendix = ' & '.join(query_appendix)
        else:
            query_appendix = ''
        
        try:
            game_count = self.multiquery('games/count', 'Game count', f'fields name; where {query_appendix};')[0]['count']
            offset = random.randint(0, game_count-1)
            query = f'fields {igdb_utilities.game_fields}; offset {offset}; limit {limit}; where {query_appendix};' 
            game_info = self.query_endpoint('games', query)
            if len(game_info) == 0:
                raise Exception
        except Exception as e:
            print(e)
        else:
            return game_info, game_count

    def get_involved_companies(self, game_id):
        query = f'fields involved_companies; where id = {game_id};'
        data = self.query_endpoint('games', query)
        
        developers, publishers = {}, {}
        company_ids = ','.join([str(id) for id in data[0]['involved_companies']])
        sub_query = f'fields company.name, developer, publisher; where id = ({company_ids});'
        company_names = self.query_endpoint('involved_companies', sub_query)
        
        for sub_dict in company_names:
            if sub_dict['developer']:
                developers[sub_dict['company']['id']] = sub_dict['company']['name']
            if sub_dict['publisher']:
                publishers[sub_dict['company']['id']] = sub_dict['company']['name']

        return developers, publishers  

    def get_multiplayer_modes(self, game_id):
        fields = igdb_utilities.multiplayer_fields
        field_map = igdb_utilities.multiplayer_field_map

        query = f'fields {fields}; where game = {game_id} & platform != null;'
        raw_data = self.query_endpoint('multiplayer_modes', query)
        multiplayer_modes = {}
        for raw in raw_data:
            temp_dict = {}
            for key,value in raw.items():
                if key == 'id' or key == 'platform' or value == False: 
                    continue
                elif value == True:
                    temp_dict[field_map[key]] = 'Yes'
                else:
                    temp_dict[field_map[key]] = value
            multiplayer_modes[raw['platform']['name']] = temp_dict
        
        return multiplayer_modes


    def get_company_info(self, input, name_or_id:str, approximate_match=True):
        
        assert (name_or_id == 'name') or (name_or_id == 'id'), "Only name or id is accepted"
        
        fields = igdb_utilities.company_fields
        
        if name_or_id == 'name':
            name_query = f'name ~ "{input}"' if not approximate_match else f'name ~ *"{input}"*'
        else:
            name_query = f'id = {input}'
        query = f'fields {fields}; where {name_query};'
        data = self.query_endpoint('companies', query)

        return data

    def get_image_url(self, id, endpoint='games', img_type='cover'):
        
        query = f'fields {img_type}.url; where id = {id};'
        data = self.query_endpoint(endpoint, query)
        url = 'https:' + data[0][img_type]['url']
        
        return url

    def get_company_games(self, company_id):
        
        company_query = f'fields name, published, developed; where id = {company_id};'
        companies = self.query_endpoint('companies', company_query)
        
        game_ids = []
        if 'developed' in companies[0].keys():
            game_ids += companies[0]['developed']*1
        if 'published' in companies[0].keys():
            game_ids += companies[0]['published']*1
        
        game_ids = set(game_ids)
        game_ids = '(' + ','.join([str(g) for g in game_ids]) + ')'
        
        game_query = f'fields name; sort rating desc; where id={game_ids} & category=0 & rating != null;'
        
        game_data = self.query_endpoint('games', game_query)
    
        games = []
        for element in game_data:
            games.append(element['name'])

        return games

    def get_all_game_modes(self):
        game_mode_list = self.query_endpoint('game_modes', 'fields name; limit 50;')
        game_mode_map = {g['name']: g['id'] for g in game_mode_list}
        return game_mode_map

    def get_all_platforms(self):
        platform_list = self.query_endpoint('platforms', 'fields name; limit 50; where platform_family = (1,2,3,4,5) & platform_family != null;')
        platform_map = {p['name']: p['id'] for p in platform_list}
        return platform_map

    def get_all_genres(self):
        genre_list = self.query_endpoint('genres', 'fields name; limit 50;')
        genre_map = {g['name']: g['id'] for g in genre_list}
        return genre_map

if __name__ == '__main__':
    wrapper = IGDBWrapper(os.environ.get('TWITCH_ID'), get_token())
    print(isinstance(wrapper, IGDBWrapper))