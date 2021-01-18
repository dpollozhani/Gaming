from igdb_authentication import get_token
import os
import sys
import inspect
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
    try:
        data = literal_eval(byte_array.decode('utf-8'))
        exception_occurred = False
    except Exception as e:
        print('==================')
        print('Warning: literal evaluation error in database query:', e, ': trying to load data as json file')
        print('Module/Function : ' + os.path.basename(__file__) + ' ' + sys._getframe().f_code.co_name +'()') 
        print('Called from     : ' + os.path.basename(inspect.stack()[1][1]) +' ' + inspect.stack()[1][3] + '()')
        exception_occurred = True
    if exception_occurred:
        data = json.loads(byte_array)

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