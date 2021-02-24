import os
import requests
from ast import literal_eval
import json
import xml.etree.ElementTree as ET
from pprint import pprint

class GamespotAPI:

    '''
        Class that handles calls to the Gamespot API
    '''

    _default_format = 'json'
    _possible_endpoints = ('games', 'releases', 'articles', 'image_galleries', 'reviews', 'videos', 'images', 'events')

    def __init__(self, api_key:str, user_agent:str):
        '''
            :_api_key: key needed to access the api
            :user_agent: must be provided as identification; Gamespot does not accept default users, e.g. "PythonLib" etc.
        '''
        self._api_key = api_key
        self.user_agent = user_agent

    def fetch_data(self, url:str):
        try:
            headers = {'user-agent': self.user_agent}
            response = requests.get(url, headers=headers)
            return json.loads(response.content)
        except requests.exceptions.RequestException as e:
            print('Error in request:', e)
        except Exception as e:
            evaluation_error = True
        if evaluation_error:
            print('Response format is not json/cannot be evaluated, returning as byte array')
            return response.content
            
    def query_endpoint(self, endpoint:str, **kwargs):
        '''
            :endpoint: specifies api endoint, e.g "games"
            :kwargs: any one of format, field_list, filter, association, sort, offset, limit.

            returns response content in wanted format.

            Example: get_data(user_agent="john_doe", format="json", field_list="id,name", filter="name:Mario kart")

            For more details, referr to https://www.gamespot.com/api/documentation#toc-0-0
        '''
        assert endpoint in self._possible_endpoints, f'endpoint must be one of {self._possible_endpoints}'

        url = f'https://www.gamespot.com/api/{endpoint}/?api_key={self._api_key}'

        if kwargs:
            appendix = '&'.join([f'{key}={value.replace(" ", "%20")}' for key, value in kwargs.items()])
            url += f'&{appendix}'
        
        print('=======')
        print(f'Sending following request:\n{url}')
        print('=======')
        
        data = self.fetch_data(url)

        return data

    def game_review(self, game:str):
        review_data = self.query_endpoint(endpoint='reviews', format=self._default_format, filter=f'title:{game}')
        return review_data

    def game_articles(self, game:str, limit='5'):
        article_data = self.query_endpoint(endpoint='articles', format=self._default_format, filter=f'title:{game}', sort='publish_date:desc', limit=limit)
        return article_data

    @property
    def possible_endpoints(self):
        return self._possible_endpoints

    @possible_endpoints.setter    
    def set_possible_endpoints(self, endpoints):
        assert isinstance(endpoints, tuple), 'possible endpoints must be a tuple of strings'
        self._possible_endpoints = endpoints

    def __repr__(self):
        hidden_key = self._api_key[:4] + ''.join(['*']*len(self._api_key[4:]))
        return f'Instance of GamespotAPI class, api_key={hidden_key}, user_agent={self.user_agent}'

if __name__ == '__main__':
    gamespot_key = os.environ.get('GAMESPOT_API_KEY')
    gs = GamespotAPI(gamespot_key, user_agent='dpollozhani')
    print(gs)
    #data = gs.query_endpoint('games', format='xml', filter='name:Ori and the blind forest')
    #pprint(data)
    # articles = gs.game_articles(game='Ori and the blind forest')
    # pprint(articles['results'])

