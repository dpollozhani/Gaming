import streamlit as st
import pandas as pd
from igdb_calls import game_info, lucky_game_info, clean_game_info, involved_companies, company_games, prompt_multiple_results, get_image_url
import os

app_mode_environment = os.environ.get('GAME_APP_MODE')
app_mode = 'test' if not app_mode_environment else app_mode_environment

#TODO: create a better design on the main info row (e.g instead of bullet lists, simple comma separated values when the list tends to get long)
@st.cache
def search(input, name_or_id='name', approximate=True):

    raw_info = game_info(input=input, name_or_id=name_or_id, approximate_match=approximate)
    
    return raw_info

def lucky():
    return lucky_game_info()

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

#Title
title = '''
    <div style ="background-color:white;padding:10px">
    <h1 style ="color:black;text-align:center;">pana$onic 2001 Game Hub</h1>
    <p style ="background-color:#b991cf;color:orange;font-style:oblique;text-align:center;">For games, look no further</p>
    </div> 
'''

st.markdown(title, unsafe_allow_html=True)

#Search bar
cols0, cols1 = st.beta_columns((4,1))
with cols0:
    search_text = st.text_input(f'Search for a game:')
with cols1:
    st.markdown('')
    st.markdown('')
    feeling_lucky = st.button('Feeling lucky')

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


try:
    if feeling_lucky:
        raw_data = lucky()
    elif len(search_text) > 0:
        multiple_results = 1
        raw_data = search(input=search_text, approximate=approximate)
        multiple_results = _prompt_multiple_results(raw_data)
        
        #Too many results matching query -> prompt to select
        if len(multiple_results) > 1:
            new_search = st.selectbox('Multiple matches were found (first is shown). Narrow down your search:', list(multiple_results.keys()))
            raw_data = search(input=multiple_results[new_search], name_or_id='id')

    if raw_data:
        #Get data
        data = _clean_game_info(raw_data[0])
        
        title, summary = ingress(data)
        image_path = _get_image_url(data['id'], endpoint='games', img_type='cover')
        
        #Header markdown
        header = f'<div><img style="float:left;margin-right:10px;", src="{image_path}", class="img-fluid"/><h2>{title}</h2>'
        if 'genres' in data.keys():
            genres = data['genres'].split(';')
            genres_text = ' '. join([genre.lower() for genre in genres])
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
                score_markdown = f'<div style="background-color:{color};width:5vw;height:55px;">'
                score_markdown += f'<p style="font-size:2vw;color:white;font-style:bold;padding:13%;text-align:center;vertical-align:middle;">{tot_score}</p></div>'
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
            st.markdown('### Released')
            if 'release_dates' in data.keys():
                st.markdown(data['release_dates'].split(';')[-1])
                remove_from_details.append('release_dates')
            else:
                st.markdown('No data available.')

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
        
