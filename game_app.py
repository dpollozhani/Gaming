import streamlit as st
#IGDB modules
from igdb.wrapper import IGDBWrapper
from igdb_authentication import authenticate_twitch, get_token
from igdb_api import IGBDAPI
from igdb_utilities import prompt_multiple_results, clean_game_info, clean_company_info
#Gamespot modules
from gamespot_api import GamespotAPI
from gamespot_utilities import clean_game_review
import pandas as pd
import os
import sys
import inspect
import json
from time import mktime
from datetime import datetime

with open('credentials/twitch_credentials.json', 'r') as f:
    twitch_expiry_days = json.load(f)['expires_in']/(3600*24)
    f.close()

credentials_updated = os.path.getmtime('credentials/twitch_credentials.json')

if (datetime.now().timestamp() - credentials_updated)/(3600*24) > twitch_expiry_days-1: #re-authenticating twich if close to expiry/has expired
    authenticate_twitch()
    st.stop()
    st.error('Wait for developer to update IGDB credentials.')

app_mode_environment = os.environ.get('GAME_APP_MODE')
app_mode = 'test' if not app_mode_environment else app_mode_environment

#################
### FUNCTIONS ###
#################

#@st.cache(allow_output_mutation=True)
def _igdb():
    wrapper = IGDBWrapper(os.environ.get('TWITCH_ID'), get_token())
    return IGBDAPI(wrapper)

#@st.cache(show_spinner=False)
def _gamespot():
    return GamespotAPI(os.environ.get('GAMESPOT_API_KEY'), user_agent='pana$onic game hub')

@st.cache(allow_output_mutation=True)
def search(input, name_or_id='name', approximate=True):
    igdb = _igdb()
    raw_info = igdb.get_game_info(input=input, name_or_id=name_or_id, approximate_match=approximate)
    return raw_info

def lucky_search(limit=1, **where_filters):
    igdb = _igdb()
    raw_info = igdb.get_lucky_game_info(limit, **where_filters)
    return raw_info

@st.cache(show_spinner=False)
def _genres():
    igdb = _igdb()
    return igdb.get_all_genres()

@st.cache(show_spinner=False)
def _game_modes():
    igdb = _igdb()
    return igdb.get_all_game_modes()

@st.cache(show_spinner=False)
def _platforms():
    igdb = _igdb()
    return igdb.get_all_platforms()

@st.cache(show_spinner=False)
def _involved_companies(game_id):
    igdb = _igdb()
    return igdb.get_involved_companies(game_id)

@st.cache(show_spinner=False)
def _company_games(company):
    igdb = _igdb()
    return igdb.get_company_games(company)

@st.cache(show_spinner=False)
def _multiplayer_modes(game_id):
    igdb = _igdb()
    return igdb.get_multiplayer_modes(game_id)

@st.cache(show_spinner=False)
def _get_image_url(id, endpoint='games', img_type='cover'):
    igdb = _igdb()
    return igdb.get_image_url(id, endpoint, img_type)

@st.cache(show_spinner=False)
def _get_game_video(id):
    igdb = _igdb()
    return igdb.get_game_video(id)

@st.cache(show_spinner=False)
def _game_review(game):
    gamespot = _gamespot()
    return gamespot.game_review(game)

@st.cache(show_spinner=False)
def _clean_game_info(info):
    return clean_game_info(info)

@st.cache(show_spinner=False)
def _clean_game_review(review):
    return clean_game_review(review)

@st.cache(show_spinner=False)
def _prompt_multiple_results(info):
    return prompt_multiple_results(info)

@st.cache(show_spinner=False)
def ingress(info):
    title, summary = '', ''
    if 'name' in info.keys():
        title = info['name']
    if 'summary' in info.keys():
        summary = info['summary']
    elif 'description' in info.keys():
        summary = info['description']
    return title, summary

@st.cache(show_spinner=False)
def score_color(score):
    if score > 69:
        color = '#2e994a'
    elif score > 40:
        color = '#d4c64e'
    else: 
        color = '#d6200f'
    return color

########################
### STREAMLIT SCRIPT ###
########################

#Page config
st.set_page_config(page_title='pana$onic 2001 game hub', page_icon='img/page_icon.jpg', layout='wide')

#Page cover
st.image('img/wallpaperflare.com_wallpaper.jpg', use_column_width=True)

#Title
title = '''
    <div style ="background-color:white;padding:10px">
    <h1 style ="color:black;text-align:center;">pana$onic 2001 Game Hub</h1>
    <p style ="background-color:#b991cf;color:orange;font-style:oblique;text-align:center;">For games, look no further</p>
    </div> 
'''

st.markdown(title, unsafe_allow_html=True)

feeling_lucky = False
genre_map = _genres()
game_mode_map = _game_modes()
platform_map = _platforms()

#Filtered search
st.markdown('#### Find a game based on filters')
col01, col02, col03 = st.beta_columns((2,2,2))
with col01:
    genre_filters = st.multiselect('Genres', list(genre_map.keys()))
    rating_filter = st.slider('Minimum rating', min_value=10, max_value=100, value=70, step=10)
with col02:    
    game_mode_filters = st.multiselect('Game mode', list(game_mode_map.keys()))
    st.markdown('<font size="2">Online</font>', unsafe_allow_html=True)
    online_mode = st.checkbox('')
with col03:
    platform_filters = st.multiselect('Platform', list(platform_map.keys()))
    year_filter = st.select_slider('Earliest release year', list(range(1985, datetime.today().year+1)), value=2010)

feeling_lucky = st.button('Lucky search')
st.markdown('-------')
where_filters, genres, game_modes = {}, '', ''

if genre_filters:
    genres = '[' + ','.join([str(genre_map[g]) for g in genre_filters]) + ']'
    where_filters['genres'] = genres
if game_mode_filters:
    game_modes = '(' + ','.join([str(game_mode_map[g]) for g in game_mode_filters]) + ')'
    where_filters['game_modes'] = game_modes
if online_mode:
    online_max = '>1'
    where_filters['multiplayer_modes.onlinemax'] = online_max
if platform_filters:
    platforms = '(' + ','.join([str(platform_map[p]) for p in platform_filters]) + ')'
    where_filters['platforms'] = platforms
if rating_filter:
    min_rating = f'>={rating_filter}'
    where_filters['rating'] = min_rating
if year_filter:
    y = int(mktime(datetime(year_filter, 1, 1).timetuple()))
    min_year = f'>={y}'
    where_filters['release_dates.date'] = min_year

#Search bar
st.markdown('#### Find a game by title')
search_text = st.text_input('Search:', value='')

#Match option and explanation
match_cols = st.beta_columns((2,5))
with match_cols[0]:
    match_type = st.select_slider('Match option (case insensitive)', ['Approximate', 'Exact'])
with match_cols[1]:    
    with st.beta_expander('?'):
        st.write('''In case approximate match yields multiple results, a list is shown. You can select from this list. 
        Sometimes approximate search can yield many unwanted results, depending on the vagueness of the search string. If so, try being more specific.
        If you are absolutely certain about the name of the game, select exact match.'''
    )
    
approximate = True if match_type=='Approximate' else False
multiple_results, raw_data = '', False

try:
    st.markdown(' ')
    if feeling_lucky: #Lucky search
        raw_data, game_count = lucky_search(**where_filters)
        st.markdown('#### Results')
        st.markdown(' ')
        st.text(f'Found {game_count} games with these constraints. Showing one of these.')
    elif len(search_text) > 0: #String search
        st.markdown('#### Results')
        st.markdown(' ')
        multiple_results = 1
        raw_data = search(input=search_text, approximate=approximate)
        multiple_results = _prompt_multiple_results(raw_data)
        
        #Too many results matching query -> prompt to select
        if len(multiple_results) > 1:
            new_search = st.selectbox('Multiple matches were found (first is shown). You may narrow down your search:', list(multiple_results.keys()))
            st.markdown('-------')
            raw_data = search(input=multiple_results[new_search], name_or_id='id')

    if raw_data:
        #Get clean data
        data = _clean_game_info(raw_data[0])
        
        title, summary = ingress(data)
        image_path = _get_image_url(data['id'], endpoint='games', img_type='cover')
        game_video = _get_game_video(data['id'])
        
        #Header markdown
        header = f'<div><img style="float:left;margin-right:10px;", src="{image_path}", class="img-fluid"/><h2>{title}</h2>'
        if 'genres' in data.keys():
            genres = data['genres'].split(';')
            genres_text = ' | '. join([genre.lower() for genre in genres])
            header += f'<p style="color:#e37e27;">{genres_text}</p>'
        header += f'<p>{summary}</p>'
        header += '</div>'
        
        st.markdown(header, unsafe_allow_html=True)

        #First info body row
        col12, col22, col32 = st.beta_columns(3)
        col13, col23, col33 = st.beta_columns(3)
        remove_from_details = []
        with col12:
            st.markdown('### Total rating')
            if 'total_rating' in data.keys():
                tot_score = round(data['total_rating'])
                color = score_color(tot_score)
                score_markdown = f'<div style="background-color:{color};width:80px;height:70px;">'
                score_markdown += f'<p style="font-size:40px;color:white;font-style:bold;margin-left:auto;margin-right:auto;text-align:center;vertical-align:middle;">{tot_score}</p></div>'
                st.markdown(score_markdown, unsafe_allow_html=True)
                remove_from_details.append('total_rating')
            else:
                st.markdown('No data available.')
        with col22:
            st.markdown('### Companies')
            if 'id' in data.keys():
                try:
                    developers, publishers = _involved_companies(data['id'])
                    got_companies = True
                except:
                    got_companies = False
                if got_companies:
                    devs_name = ', '.join(list(developers.values()))
                    pubs_name = ', '.join(list(publishers.values()))
                    devs_id = list(developers.keys())
                    pubs_id = list(publishers.keys())
                    st.markdown(f'**Developer**: {devs_name}')
                    st.markdown(f'**Publisher**: {pubs_name}')
                else:
                    st.markdown('No data available')
            else:
                st.markdown('No data available.')
        with col32:
            st.markdown('### Available on')
            if 'platforms' in data.keys():
                st.markdown(data['platforms'])
                remove_from_details.append('platforms')
            else:
                st.markdown('No data available.')
            
        #Second info body row
        with col13:
            st.markdown('### Game modes')
            if 'game_modes' in data.keys():
                st.markdown(data['game_modes'])
                remove_from_details.append('game_modes')
            else:
                st.markdown('No data available.')
        with col23:
            st.subheader('Age recommendation')
            if 'age_ratings' in data.keys():
                st.markdown(data['age_ratings'])
                remove_from_details.append('age_ratings')
            else:
                st.markdown('No data available.')
        with col33:
            st.markdown('### First released')
            if 'release_dates' in data.keys():
                released = sorted(data['release_dates'].split(';'), key=lambda x: x.split(',')[-1])[0]
                st.markdown(released)
                remove_from_details.append('release_dates')
            else:
                st.markdown('No data available.')
        
        #Video
        if len(game_video) > 0:
            st.video(game_video)

        #Reviews
        review_data = _game_review(title)
        if len(review_data['results']) > 0: 
            review_block = st.beta_container()
            with review_block:
                st.subheader('Review')
                review_summary = review_data['results'][0]['deck']
                review_author = review_data['results'][0]['authors']
                review_positives = review_data['results'][0]['good']
                review_negatives = review_data['results'][0]['bad']
                review_date = review_data['results'][0]['update_date'].split(' ')[0]
                st.markdown(f'"*{review_summary}*"')
                st.markdown(f':thumbsup: {review_positives.replace("|",  " | ")}')
                st.markdown(f':thumbsdown: {review_negatives.replace("|",  " | ")}')
                st.markdown(f'-**{review_author}** (Gamespot, {review_date})')
                review_expander = st.beta_expander('Full review')
                with review_expander:
                    review_body = _clean_game_review(review_data['results'][0]['body'])
                    st.markdown(review_body, unsafe_allow_html=True)
                
        st.subheader('More info')

        #Expand for multiplayer modes
        multi_modes = _multiplayer_modes(data['id'])
        print(multi_modes)
        if multi_modes:
            with st.beta_expander('Multiplayer modes'):
                for m, vals in multi_modes.items():
                    v = [f'{x[0]}: {x[1]}' for x in vals.items()]    
                    bullets = f'* {m}: \n'
                    for w in v:
                        bullets += f'  * {w}\n'
                    st.markdown(bullets)

        #Expand for similar games        
        if 'similar_games' in data.keys(): 
            with st.beta_expander('Similar games'):
                for game in data['similar_games'].split(';'):
                    st.markdown(f'* {game}')
            remove_from_details.append('similar_games')

        #Expand for other games by developer
        if got_companies:
            for dev_id in devs_id:
                dev_games = _company_games(dev_id)
            for pub_id in pubs_id:
                pub_games = _company_games(pub_id)
            other_games = sorted(list(set(dev_games + pub_games) - {title}))
            with st.beta_expander('Other games by this developer/publisher'):
                for other_game in other_games:
                    st.markdown(f'* {other_game}')        

        #Expand for game engine
        if 'game_engines' in data.keys(): 
            with st.beta_expander('Engine(s)'):
                for engine in data['game_engines'].split(';'):
                    st.markdown(f'* {engine}')
            remove_from_details.append('game_engines')

        #Expand for keywords
        if 'keywords' in data.keys():
            with st.beta_expander('Keywords'):
                st.markdown(data['keywords'])
            remove_from_details.append('keywords')
        
        for i in ['id', 'summary', 'name', 'genres']:
            remove_from_details.append(i)

        #Expand for further details        
        with st.beta_expander('Further details'):
            for key, value in data.items():
                if key not in remove_from_details:
                    st.markdown('* ' + '**' + str(key) + '**: ' + str(value), unsafe_allow_html=True)

except Exception as e:
    print(e)
    print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
    print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')