### LIBRARIES
import os  
import traceback
import pandas as pd
import numpy as np
import networkx
from networkx.algorithms import community
import matplotlib.pyplot as plt
from bokeh.io import show, save
from bokeh.models import Range1d, TapTool, BoxSelectTool, Circle, MultiLine, EdgesAndLinkedNodes, NodesAndLinkedEdges
from bokeh.plotting import figure
from bokeh.plotting import from_networkx
from bokeh.palettes import Spectral11
import streamlit as st

global_max_year = 2021

st.set_page_config(page_title='pana$onic 2001 game hub', page_icon='img/page_icon.jpg', layout='wide')

### DATA
@st.cache(show_spinner=False)
def _get_edges(from_year):
    #to_year = from_year + 1
    edges_tmp = []
    for file in os.listdir('data/'):
        if f'company_edges_{from_year}' in file:
            data = pd.read_csv(f'data/{file}')
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
            nodes_tmp.append(pd.read_csv(f'data/{file}'))
    nodes = pd.concat(nodes_tmp, ignore_index=True)
    nodes.drop_duplicates(inplace=True)
    ids = [id for id in nodes.id.values]
    names = [name for name in nodes.name.values]
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

def _load_graph(from_year):
    edges = _get_edges(from_year)
    nodes = _get_node_names(from_year)
    G = _generate_network(edges)
    G = _set_node_names(G, nodes)
    G, degrees = _degree(G)
    communities = _community(G)
    return G, edges, nodes, degrees, communities

def _plot_network(from_year):
    
    G, _, nodes, degrees, communities = _load_graph(from_year)

    total_nodes = networkx.number_of_nodes(G)
    total_edges = networkx.number_of_edges(G)
    avg_degree = round(np.mean(list(degrees.values())), 2)
    
    sorted_degrees = dict(sorted(degrees.items(), key=lambda item: item[1], reverse=True))
    top_degree_keys = list(sorted_degrees.keys())[:5]
    top_degrees = {nodes[k]: sorted_degrees[k] for k in top_degree_keys}
    modularity_classes = len(communities)

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
    plot_title = f'Collaborative structure between {from_year} and {global_max_year}'
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
    network_graph.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)
    #Set edge highlight colors
    network_graph.edge_renderer.selection_glyph = MultiLine(line_color=edge_highlight_color, line_width=2)
    network_graph.edge_renderer.hover_glyph = MultiLine(line_color=edge_highlight_color, line_width=2)

    #Highlight nodes and edges
    network_graph.selection_policy = NodesAndLinkedEdges()
    network_graph.inspection_policy = NodesAndLinkedEdges()

    #Add network graph to the plot
    plot.renderers.append(network_graph)

    st.bokeh_chart(plot, use_container_width=True)

    return avg_degree, top_degrees, modularity_classes, total_nodes, total_edges
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
    from_year = st.selectbox('Select year: ', [2018, 2019, 2020], index=2)

try:
    avg_degree, top_degrees, modularity_classes, total_nodes, total_edges = _plot_network(from_year)
    network_info = st.beta_container()
    with network_info:
        st.markdown('#### Most collabs:')
        s = []
        for k,v in top_degrees.items():
            s.append(f'{k}: {v}')
        st.markdown(' | '.join(s))
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
except FileNotFoundError as e:
    print(e)
    st.error('For the time being, data for this year is missing. Working on it!')
except:
    traceback.print_exc()