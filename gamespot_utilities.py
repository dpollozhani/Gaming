import re

def clean_game_review(review:str):
    video_pattern = r'(<div data-embed-type="video".*?</div>)'
    review = re.sub(video_pattern, '', review)
    review = review.replace('<a ', '<a target="_blank" ')
    return review


if __name__ == '__main__':
    from gamespot_api import GamespotAPI
    import os
    from pprint import pprint
    import re
    gs = GamespotAPI(os.environ.get('GAMESPOT_API_KEY'), user_agent='dpollozhani')
    data = gs.game_review('Ori and the will of the wisps')
    review = data['results'][0]['body']
    print(clean_game_review(review))
    
 
