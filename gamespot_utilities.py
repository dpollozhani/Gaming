import re

def clean_game_review(review:str):
    pattern = r'(<div data-embed-type="video".*?</div>)'
    review = re.sub(pattern, '', review)

    return review

if __name__ == '__main__':
    from gamespot_api import GamespotAPI
    import os
    from pprint import pprint
    import re
    gs = GamespotAPI(os.environ.get('GAMESPOT_API_KEY'), user_agent='dpollozhani')
    data = gs.game_review('Ori and the will of the wisps')
    print(data['results'][0]['good'])
    print(data['results'][0]['bad'])
    # pattern = r'(<div data-embed-type="video".*?</div>)'
    # review = re.sub(pattern, '', review) #search(review).groups())
    # pprint(review)
    
 
