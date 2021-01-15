from igdb_authentication import get_token
import os
import json
from ast import literal_eval
from igdb.wrapper import IGDBWrapper
#from igdb.igdbapi_pb2 import GameResult

def get_data(endpoint:str, query:str):
    wrapper = IGDBWrapper(os.environ.get('TWITCH_ID'), get_token())

    byte_array = wrapper.api_request(
                endpoint,
                query 
                )
    
    data = literal_eval(byte_array.decode('utf-8'))

    return data

def to_json(data, outfile, indent=3):
    if not '.json' in outfile:
        outfile += '.json'
    with open(outfile, 'w') as f:
        json.dump(data, f, indent=indent)
        f.close()

def open_json(infile):
    with open(infile, 'r') as f:
        data = json.load(f)
        f.close()
    return data