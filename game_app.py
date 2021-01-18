import streamlit as st
import pandas as pd
from igdb_calls import game_info, clean_game_info, involved_companies, company_games, prompt_multiple_results, get_image_url
import os

app_mode_environment = os.environ.get('GAME_APP_MODE')
app_mode = 'test' if not app_mode_environment else app_mode_environment

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

#Title
title = '''
    <div style ="background-color:white;padding:10px">
    <h1 style ="color:black;text-align:center;">pana$onic 2001 Game Hub</h1>
    <p style ="background-color:#b991cf;color:orange;font-style:oblique;text-align:center;">For games, look no further</p>
    </div> 
'''

st.markdown(title, unsafe_allow_html=True)

#Search bar
search_text = st.text_input(f'Search for a game:')

#Match option and explanation
col01, _, col03= st.beta_columns(3)
with col01:
    match_type = st.select_slider('Match option (case insensitive)', ['Approximate', 'Exact'])
with col03:
    with st.beta_expander('?'):
        st.write('''In case approximate match yields multiple results, a list is shown. You can select from this list. 
        Sometimes approximate search can yield many unwanted results, based on the vagueness of the search string. If so, try being more specific.
        If you are absolutely certain about the name of the game, select exact match,'''
    )

approximate = True if match_type=='Approximate' else False
multiple_results, raw_data = '', False

#Main block
try:
    if len(search_text) > 0:
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
            st.markdown('### Critic metascore')
            if 'aggregated_rating' in data.keys():
                score = round(data['aggregated_rating'])
                if score > 69:
                    color = '#2e994a'
                elif score > 40:
                    color = '#d4c64e'
                else: 
                    color = '#d6200f'
                score_markdown = f'<div style="background-color:{color};width:50px;height:55px;">'
                score_markdown += f'<p style="font-size:25px;color:white;font-style:bold;padding:20%;text-alignment:center;">{score}</p></div>'
                st.markdown(score_markdown, unsafe_allow_html=True)
                remove_from_details.append('aggregated_rating')
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
                for p in data['platforms'].split(';'):
                    st.markdown(f'{p}')
                remove_from_details.append('platforms')
            else:
                st.markdown('No data available.')
            
        #Second info body row
        with col13:
            st.markdown('### Game modes')
            if 'game_modes' in data.keys():
                for game_m in data['game_modes'].split(';'):
                    st.markdown(f'{game_m}')
                remove_from_details.append('game_modes')
            else:
                st.markdown('No data available.')
        with col23:
            st.subheader('Age rating')
            if 'age_ratings' in data.keys():
                for age_r in data['age_ratings'].split(';'):
                    st.markdown(f'{age_r}')
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
        
