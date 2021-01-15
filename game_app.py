import streamlit as st
import pandas as pd
from igdb_calls import game_info, clean_game_info, company_info, clean_company_info, prompt_multiple_results, get_image_url
from pathlib import Path
import base64

mode = 'test' #prod

@st.cache
def search(input, name_or_id='name', approximate=True):

    raw_info = game_info(input=input, name_or_id=name_or_id, approximate_match=approximate)
    
    return raw_info

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

def keep(df, to_keep, chosen_view):
    fields_to_keep = sorted(list(set(to_keep).intersection(set(df['Details'].values))))
    return df[df['Details'].isin(fields_to_keep)]

@st.cache
def render(info, filters=None):
    df = pd.DataFrame.from_dict(info, orient='index')
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Details', 0: ''}, inplace=True)
    df = drop(df, ['id', 'summary', 'name', 'description'])
    if filters:
        df = drop(df, filters)
    return df

def get_possible_filters(info):
    return list(set(info.keys()))

st.title('pana$onic 2001 Game Hub')

#Search bar
search_text = st.text_input(f'Search for a game:')

#Match option
col01, _, col03= st.beta_columns(3)
with col01:
    match_type = st.select_slider('Match option (case insensitive)', ['Approximate', 'Exact'])
with col03:
    with st.beta_expander('?'):
        st.write('In case approximate search yields multiple results, a list is shown. If you get several matches with approximate search and you find what you were looking for in the list, you can choose "exact match" as a shortcut to search for that particular game.')

approximate = True if match_type=='Approximate' else False

try:
    if len(search_text) > 0:
        raw_data = search(input=search_text, approximate=approximate)
        multiple_results = prompt_multiple_results(raw_data)
        
        #Too many results matching query -> prompt to select
        if len(multiple_results) > 1:
            search_text = st.selectbox('Multiple matches were found (first is shown). Narrow down your search:', list(multiple_results.keys()))
            raw_data = search(input=multiple_results[search_text], name_or_id='id')

        #Get data
        data = clean_game_info(raw_data[0])
        
        title, summary = ingress(data)
        image_path = get_image_url(data['id'], endpoint='games', img_type='cover')
        header = f'<div><img style="float:right;", src="{image_path}", class="img-fluid"/><h2 style:"float:left;">{title}</h2><p>{summary}</p></div>'
        
        st.markdown(header, unsafe_allow_html=True)
    
        col12, col22, col32 = st.beta_columns(3)
        col13, col23, col33 = st.beta_columns(3)
        remove_from_details = []
        #First info row
        with col12:
            st.subheader('Age rating')
            if 'age_ratings' in data.keys():
                for age_r in data['age_ratings'].split(';'):
                    st.markdown(f'* {age_r}')
                remove_from_details.append('age_ratings')
            else:
                st.markdown('No data available.')
        with col22:
            st.markdown('### Critic metascore')
            if 'aggregated_rating' in data.keys():
                st.markdown(str(round(data['aggregated_rating'])))
                remove_from_details.append('aggregated_rating')
            else:
                st.markdown('No data available.')
        with col32:
            st.markdown('### Released')
            if 'release_dates' in data.keys():
                st.markdown(data['release_dates'].split(';')[-1])
                remove_from_details.append('release_dates')
            else:
                st.markdown('No data available.')
            
        #Second info row
        with col13:
            st.markdown('### Genres')
            if 'genres' in data.keys():
                for genre in data['genres'].split(';'):
                    st.markdown(f'* {genre}')
                remove_from_details.append('genres')
            else:
                st.markdown('No data available.')
        with col23:
            st.markdown('### Game modes')
            if 'game_modes' in data.keys():
                for game_m in data['game_modes'].split(';'):
                    st.markdown(f'* {game_m}')
                remove_from_details.append('game_modes')
            else:
                st.markdown('No data available.')
        with col33:
            st.markdown('### Available on')
            if 'platforms' in data.keys():
                for p in data['platforms'].split(';'):
                    st.markdown(f'* {p}')
                remove_from_details.append('platforms')
            else:
                st.markdown('No data available.')
        
        #Expand for similar games        
        if 'similar_games' in data.keys(): 
            with st.beta_expander('Similar games'):
                for game in data['similar_games'].split(';'):
                    st.markdown(f'* {game}')
            remove_from_details.append('similar_games')
        
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

        #Expand for further details        
        with st.beta_expander('Further details'):
            df = render(data, filters=remove_from_details)
            df.rename(columns={'Details': ''}, inplace=True)
            st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
except Exception as e:
    st.error('Something went wrong. Please try again, for instance by changing match option or re-writing your query.')
    if mode == 'test':
        error_details = st.button('Show more details')
        if error_details:
            st.write(e)
        
