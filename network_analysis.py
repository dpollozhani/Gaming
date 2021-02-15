### LIBRARIES
import os  
import traceback
import pandas as pd
import numpy as np
import copy
import networkx
from networkx.algorithms import community
from networkx.algorithms import shortest_path
from networkx.exception  import NetworkXNoPath
#import matplotlib.pyplot as plt
from bokeh.io import show, save
from bokeh.models import Range1d, TapTool, BoxSelectTool, Circle, MultiLine, EdgesAndLinkedNodes, NodesAndLinkedEdges, CustomJS, Slider, Column
from bokeh.plotting import figure
from bokeh.plotting import from_networkx
from bokeh.palettes import Spectral11
import streamlit as st

global_max_year = 2021

st.set_page_config(page_title='pana$onic 2001 game network', page_icon='img/page_icon.jpg', layout='wide')

### DATA
@st.cache(show_spinner=False)
def _load_involved_companies(from_year):
    tmp = []
    for file in os.listdir('data/'):
        if f'involved_companies_{from_year}' in file:
            data = pd.read_csv(f'data/{file}', delimiter=';')
            tmp.append(data)
    df = pd.concat(tmp, ignore_index=True)
    return df

@st.cache(show_spinner=False)
def _get_company_games(from_year, companies):
    games_df = _load_involved_companies(from_year)
    games = []
    for _, row in games_df.iterrows():
        these_companies = set(row['companies'].split(','))
        if set(these_companies).issuperset([str(c) for c in companies]):
            games.append(row['game_name'])
    return games

def _get_game_companies(from_year, game_name):
    company_df = _load_involved_companies(from_year)
    company_ids = company_df[company_df['game_name'].str.match(game_name, case=False)]['companies'].values
    return company_ids


@st.cache(show_spinner=False)
def _get_edges(from_year):
    #to_year = from_year + 1
    edges_tmp = []
    for file in os.listdir('data/'):
        if f'company_edges_{from_year}' in file:
            data = pd.read_csv(f'data/{file}', delimiter=';')
            edges_tmp.append(data)
    edges = pd.concat(edges_tmp, ignore_index=True)
    edges.drop_duplicates(inplace=True)
    return edges

@st.cache(show_spinner=False)
def _get_node_names(from_year):
    #to_year = from_year + 1
    nodes_tmp = []
    for file in os.listdir('data'):
        if f'company_nodes_{from_year}' in file:
            nodes_tmp.append(pd.read_csv(f'data/{file}', delimiter=';'))
    nodes = pd.concat(nodes_tmp, ignore_index=True)
    nodes.drop_duplicates(inplace=True)
    ids = [id for id in nodes['id'].values]
    names = [name for name in nodes['name'].values]
    return dict(zip(ids, names))

### GRAPH
@st.cache(allow_output_mutation=True)
def _generate_network(edges):
    G = networkx.from_pandas_edgelist(edges, 'source', 'target')
    return G

@st.cache(show_spinner=False, allow_output_mutation=True)
def _set_node_names(G, name_dict):
    networkx.set_node_attributes(G, name='name', values=name_dict)
    return G

@st.cache(show_spinner=False)
def _degree(G):
    # Calculate network degree and add as node attribute
    degrees = dict(networkx.degree(G))
    networkx.set_node_attributes(G, name='degree', values=degrees)
    # Adjustment of degree for visibility of small nodes
    number_to_adjust_by = 5
    adjusted_node_size = dict([(node, degree+number_to_adjust_by) for node, degree in networkx.degree(G)])
    networkx.set_node_attributes(G, name='adjusted_node_size', values=adjusted_node_size)
    return G, degrees

@st.cache(show_spinner=False)
def _community(G):
    # Communities in network
    communities = community.greedy_modularity_communities(G)
    return communities

@st.cache(show_spinner=False, allow_output_mutation=True)
def _load_graph(from_year):
    edges = _get_edges(from_year)
    nodes = _get_node_names(from_year)
    G = _generate_network(edges)
    G = _set_node_names(G, nodes)
    G, degrees = _degree(G)
    communities = _community(G)
    return G, edges, nodes, degrees, communities

def _find_shortest_path(G, source, target):
    try:
        shortest_p = shortest_path(G, source, target)
    except NetworkXNoPath as e:
        return e
    else:
        return shortest_p

def _plot_network(from_year):
    
    G, _, nodes, degrees, communities = _load_graph(from_year)

    #Choose colors for node and edge highlighting
    node_highlight_color = 'white'
    edge_highlight_color = 'black'

    #Choose attributes from G network to size and color by — setting manual size (e.g. 10) or color (e.g. 'skyblue') also allowed
    size_by_this_attribute = 'adjusted_node_size'
    color_by_this_attribute = 'modularity_color'
  
    # Modularity class and colors
    modularity_class = {}
    modularity_color = {}
    #Loop through each community in the network
    for community_number, community in enumerate(communities):
        #For each member of the community, add their community number and a distinct color
        for name in community: 
            modularity_class[name] = community_number
            modularity_color[name] = Spectral11[min(len(Spectral11)-1,community_number)]
    
    #Graph metrics to be shown below plot
    total_nodes = networkx.number_of_nodes(G)
    total_edges = networkx.number_of_edges(G)
    avg_degree = round(np.mean(list(degrees.values())), 2)
    
    sorted_degrees = dict(sorted(degrees.items(), key=lambda item: item[1], reverse=True))
    top_degree_keys = list(sorted_degrees.keys())[:5]
    top_degrees = {nodes[k]: (sorted_degrees[k], modularity_class[k], modularity_color[k]) for k in top_degree_keys}

    modularity_classes = len(communities)    

    # Add modularity class and color as attributes from the network above
    networkx.set_node_attributes(G, modularity_class, 'modularity_class')
    networkx.set_node_attributes(G, modularity_color, 'modularity_color')

    #Establish which categories will appear when hovering over each node
    HOVER_TOOLTIPS = [
            ("Company", "@index"),
            ("Name", "@name"),
            ("Degree", "@degree"),
            ("Modularity Class", "@modularity_class")]

    #to_year = from_year + 1
    plot_title = f'Collaborative structure between {from_year} and {from_year+1}'
    #Create a plot — set dimensions, toolbar, and title
    plot = figure(tooltips = HOVER_TOOLTIPS,
                tools="pan,wheel_zoom,save,reset", active_scroll='wheel_zoom',
                x_range=Range1d(-10.1, 10.1), y_range=Range1d(-10.1, 10.1), title=plot_title)

    plot.add_tools(TapTool(), BoxSelectTool())
    
    #Create a network graph object with spring layout
    # https://networkx.github.io/documentation/networkx-1.9/reference/generated/networkx.drawing.layout.spring_layout.html
    network_graph = from_networkx(G, networkx.spring_layout, scale=10, center=(0, 0))

    #Set node size and color
    network_graph.node_renderer.glyph = Circle(size=size_by_this_attribute, fill_color=color_by_this_attribute)
    #Set node highlight colors
    network_graph.node_renderer.hover_glyph = Circle(size=size_by_this_attribute, fill_color=node_highlight_color, line_width=2)
    network_graph.node_renderer.selection_glyph = Circle(size=size_by_this_attribute, fill_color=node_highlight_color, line_width=2)
    

    #Set edge opacity and width
    network_graph.edge_renderer.glyph = MultiLine(line_alpha=0, line_width=1)
    #Set edge highlight colors
    network_graph.edge_renderer.selection_glyph = MultiLine(line_color=edge_highlight_color, line_width=2)
    network_graph.edge_renderer.hover_glyph = MultiLine(line_color=edge_highlight_color, line_width=2)

    #Highlight nodes and edges
    network_graph.selection_policy = NodesAndLinkedEdges()
    network_graph.inspection_policy = NodesAndLinkedEdges()

    #Add network graph to the plot
    plot.renderers.append(network_graph)

    return plot, G, nodes, avg_degree, top_degrees, modularity_classes, total_nodes, total_edges 
    #show(plot)
    #save(plot, filename=f"{title}.html")

### VIZ
title = 'Game company network'
st.title(title)

st.markdown('Network analysis of game company collaboration. \
A collaboration means that two companies have worked together to produce games in developing, publishing, porting, supporting roles, or several of these.\
    Analyzing the network might show which companies are most prolific, have most influence or potentially give an indication of market share.')

year_selection = st.beta_columns((2, 5))
with year_selection[0]:
    from_year = st.selectbox('Select year: ', [2016, 2017, 2018, 2019, 2020], index=4)



try:
    plot, G, nodes, avg_degree, top_degrees, modularity_classes, total_nodes, total_edges = _plot_network(from_year)
    company_ids = {str(v): k for k,v in nodes.items()}
    st.bokeh_chart(plot, use_container_width=True)
    network_info = st.beta_container()
    with network_info:
        st.markdown('#### Most collabs:')
        s = []
        for company,values in top_degrees.items():
            text = f'{company}: {values[0]} (Community: {values[1]})'
            s.append(text)
        st.markdown(' | '.join(s), unsafe_allow_html=True)
        network_info_cols = st.beta_columns((2,2,2,2))
        with network_info_cols[0]:
            st.markdown('#### Average collabs per company:') 
            st.markdown(avg_degree)
        with network_info_cols[1]:
            st.markdown('#### Communities:')
            st.markdown(modularity_classes)
        with network_info_cols[2]:
            st.markdown('#### Total companies:')
            st.markdown(total_nodes)
        with network_info_cols[3]:
            st.markdown('#### Total collabs:')
            st.markdown(total_edges)
        st.markdown('-------')
        st.markdown('#### Find shortest network path ("friends of friends") between *two* companies *(separate with semi-colon)*:')
        sp_source_target = st.text_input('Companies:', key=2)
        if sp_source_target.count(';') == 1 and len(sp_source_target.split(';')) > 1:
            sp_source = sp_source_target.split(';')[0].strip(' ')
            sp_target = sp_source_target.split(';')[1].strip(' ')
            s = company_ids[sp_source] if sp_source in company_ids.keys() else None
            t = company_ids[sp_target] if sp_target in company_ids.keys() else None
            print(s, t)
            if all([s,t]):
                shortest_path_tmp = _find_shortest_path(G, s, t)
                if not isinstance(shortest_path_tmp, NetworkXNoPath):
                    shortest_path_length = max(0,len(shortest_path_tmp)-2)
                    st.markdown(f'*There are {shortest_path_length} companies between {sp_source} and {sp_target}*.')
                    shortest_path = ' --> '.join([nodes[p] for p in shortest_path_tmp])
                else:
                    shortest_path = 'No path exists between these companies.'
                st.markdown(shortest_path)
            else:
                st.error('One or more of the companies were not found, or too few companies were submitted.')
        st.markdown('-------')
        st.markdown('#### Find which games a *pair* of companies worked together on *(separate with semi-colon)*:')
        games_companies = st.text_input('Companies:', key=1)
        if games_companies.count(';') == 1 and len(games_companies.split(';')) > 1:
            first = games_companies.split(';')[0].strip(' ')
            second = games_companies.split(';')[1].strip(' ')
            f = company_ids[first] if first in company_ids.keys() else None
            s = company_ids[second] if second in company_ids.keys() else None
            print(f, s)
            if all([f,s]):
                collab_games = _get_company_games(from_year, [f,s])
                if len(collab_games) > 0:
                    st.markdown('; '.join(collab_games))
                else:
                    st.markdown(f'These companies have not collaborated on any game during {from_year}')
        st.markdown('-------')
        st.markdown('#### Find which companies worked together on a game:')
        companies_game = st.text_input('Game name:')
        companies_ = _get_game_companies(from_year, companies_game)
        if len(companies_) > 0:
            nodes_str_map = {str(k): v for k,v in nodes.items()}
            company_names = '; '.join([nodes_str_map[c] for company in companies_ for c in company.split(',')])
            st.markdown(company_names)
        else:
            st.markdown('Game was not found. It could have been released another year.')
        list_of_companies = st.beta_expander(f'List of all companies that have been part of at least one collaboration between {from_year} and {from_year+1}:')
        with list_of_companies:
            company_list = '; '.join(sorted(list(nodes.values())))
            st.markdown(company_list)
except FileNotFoundError as e:
    print(e)
    st.error('For the time being, data for this year is missing. Working on it!')
except:
    traceback.print_exc()