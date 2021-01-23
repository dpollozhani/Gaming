import streamlit as st
import pandas as pd
from igdb_calls import game_info, lucky_game_info, clean_game_info
from igdb_calls import involved_companies, company_games, multiplayer_modes, prompt_multiple_results, get_image_url
from igdb_calls import get_game_modes, get_genres, get_platforms
import os
from time import mktime
from datetime import datetime

app_mode_environment = os.environ.get('GAME_APP_MODE')
app_mode = 'test' if not app_mode_environment else app_mode_environment

@st.cache(show_spinner=False)
def _genres():
    return get_genres()

@st.cache(show_spinner=False)
def _game_modes():
    return get_game_modes()

@st.cache(show_spinner=False)
def _platforms():
    return get_platforms()

@st.cache
def search(input, name_or_id='name', approximate=True):

    raw_info = game_info(input=input, name_or_id=name_or_id, approximate_match=approximate)
    
    return raw_info

@st.cache(show_spinner=False)
def _clean_game_info(info):
    return clean_game_info(info)

@st.cache(show_spinner=False)
def _prompt_multiple_results(info):
    return prompt_multiple_results(info)

@st.cache(show_spinner=False)
def _involved_companies(game_id):
    return involved_companies(game_id)

@st.cache(show_spinner=False)
def _company_games(company):
    return company_games(company)

@st.cache(show_spinner=False)
def _multiplayer_modes(game_id):
    return multiplayer_modes(game_id)

@st.cache(show_spinner=False)
def _get_image_url(id, endpoint='games', img_type='cover'):
    return get_image_url(id, endpoint, img_type)

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

def drop(df, to_drop):
    for d in to_drop:
        df = df[df['Details'] != d]
    return df

def keep(df, to_keep):
    fields_to_keep = sorted(list(set(to_keep).intersection(set(df['Details'].values))))
    return df[df['Details'].isin(fields_to_keep)]

@st.cache(show_spinner=False)
def render(info, filters=None):
    df = pd.DataFrame.from_dict(info, orient='index')
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Details', 0: ''}, inplace=True)
    df = drop(df, ['id', 'summary', 'name', 'description'])
    if filters:
        df = drop(df, filters)
    return df.set_index('Details').transpose()

@st.cache(show_spinner=False)
def score_color(score):
    if score > 69:
        color = '#2e994a'
    elif score > 40:
        color = '#d4c64e'
    else: 
        color = '#d6200f'
    return color

#Page config
st.set_page_config(page_title='pana$onic 2001 game hub', page_icon='img/page_icon.jpg')

#Page cover
st.image('img/ori1.jpg', use_column_width=True,)

#Title
title = '''
    <div style ="background-color:white;padding:10px">
    <h1 style ="color:black;text-align:center;">pana$onic 2001 Game Hub</h1>
    <p style ="background-color:#b991cf;color:orange;font-style:oblique;text-align:center;">For games, look no further</p>
    </div> 
'''

st.markdown(title, unsafe_allow_html=True)

#Search bar
search_text = st.text_input('Search for a game (or expand left side bar for filtered search):')

feeling_lucky = False

#Match option and explanation
col01, _, col02 = st.beta_columns((2,2,2))
with col01:
    match_type = st.select_slider('Match option (case insensitive)', ['Approximate', 'Exact'])
with col02:
    with st.beta_expander('?'):
        st.write('''In case approximate match yields multiple results, a list is shown. You can select from this list. 
        Sometimes approximate search can yield many unwanted results, depending on the vagueness of the search string. If so, try being more specific.
        If you are absolutely certain about the name of the game, select exact match.'''
    )

approximate = True if match_type=='Approximate' else False
multiple_results, raw_data = '', False

genre_map = _genres()

game_mode_map = _game_modes()

platform_map = _platforms()

#Side bar
side_bar = st.sidebar.beta_container()
with side_bar:
    st.markdown('## Lucky Luke')
    st.markdown('Try controlling your luck:')
    genre_filters = st.multiselect('Genres', list(genre_map.keys()))
    game_mode_filters = st.multiselect('Game mode', list(game_mode_map.keys()))
    st.markdown('<font size="2">Online</font>', unsafe_allow_html=True)
    online_mode = st.checkbox('')
    platform_filters = st.multiselect('Platform', list(platform_map.keys()))
    rating_filter = st.slider('Minimum rating', min_value=10, max_value=100, value=70, step=10)
    year_filter = st.select_slider('Earliest release year', list(range(1985, datetime.today().year+1)), value=2010)
    feeling_lucky = st.button('Lucky search')
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
try:
    if feeling_lucky: #Lucky search
        raw_data, game_count = lucky_game_info(**where_filters)
        with side_bar:
            st.text(f'Found {game_count} games with these constraints.')
    elif len(search_text) > 0: #String search
        multiple_results = 1
        raw_data = search(input=search_text, approximate=approximate)
        multiple_results = _prompt_multiple_results(raw_data)
        
        #Too many results matching query -> prompt to select
        if len(multiple_results) > 1:
            new_search = st.selectbox('Multiple matches were found (first is shown). Narrow down your search:', list(multiple_results.keys()))
            raw_data = search(input=multiple_results[new_search], name_or_id='id')

    if raw_data:
        #Get clean data
        data = _clean_game_info(raw_data[0])
        
        title, summary = ingress(data)
        image_path = _get_image_url(data['id'], endpoint='games', img_type='cover')
        
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
                #for p in data['platforms'].split(';'):
                #    st.markdown(f'{p}')
                remove_from_details.append('platforms')
            else:
                st.markdown('No data available.')
            
        #Second info body row
        with col13:
            st.markdown('### Game modes')
            if 'game_modes' in data.keys():
                st.markdown(data['game_modes'])
                #for game_m in data['game_modes'].split(';'):
                #    st.markdown(f'{game_m}')
                remove_from_details.append('game_modes')
            else:
                st.markdown('No data available.')
        with col23:
            st.subheader('Age recommendation')
            if 'age_ratings' in data.keys():
                st.markdown(data['age_ratings'])
                #for age_r in data['age_ratings'].split(';'):
                #    st.markdown(f'{age_r}')
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

        #Expand for multiplayer modes
        multi_modes = _multiplayer_modes(data['id'])
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
    #st.error('Something went wrong. Content not available.')
    print(e)
        
