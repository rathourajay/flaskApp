## Library for webscraping, delimiting etc
## Alex Lee 2016 - Work in progress

import requests
import pandas as pd
from lxml import html
import json

# Takes some text, a dictionary and a list of strings.
# The text contains scraped data that we are interested in delimiting
# the dictionary is the 'Data Hierarchy' that specified where in the text the relevant data is located
# the keylist is a list of strings that specifies where in the data the list of locations is
def json_bundle(data_json, dict_data, keylist):
    # the titles of the columns that should appear in the output
    col_titles = dict_data.keys()
    
    # initialise the 'data bundle'
    data = {}
    for col in col_titles:
        data[col] = []
    
    # extract location list
    locations = dict_descent( json.loads(get_json(data_json)), keylist )
    
    # ensures that we are actually extracting locations from the data, otherwise just return a dictionary with no data
    if locations == 'Error: No such path in dictionary':
        return data
    else:
        num_locations = len(locations)
        # run through each of the column titles and add in the data
        for col in col_titles:
            # look for the path that specifies where that column's data is located
            value = dict_data[col]
            for i in range(0, num_locations):
                data[col].append( dict_descent(locations[i], value ) )
        return data

# takes some text and a dictionary whose values specify the xml path of the corresponding data field.
def html_bundle(data_html, dict_paths):
    #    column_titles = ['Brand', 'Site Reference', 'Title', 'Address', 'Suburb', 'State',
    #                    'Postcode', 'Country', 'Latitude', 'Longitude', 'Phone']
    
    column_titles = dict_paths.keys()
    
    # parse the html and make a tree
    tree = html.fromstring( bytes(data_html, 'utf-8') )
    
    # determine the number of locations based on the maximum number of values that match a path
    max_len = 0
    for key in dict_paths.keys():
        if dict_paths[key] == '':
            pass
        else:
            if is_path(dict_paths[key]):
                max_len = max(max_len, len( path_to_data(data_html, dict_paths[key]) ))

    # number of locations (does this always work?)
    num_locations = max_len
    
    # initialise the 'data bundle'
    dict_out = {}
    for col in column_titles:
        dict_out[col] = []

    # run through each of the column titles and extract the relevant data
    for col in column_titles:
        # if the path starts with ### it is some sort of non-html embedded in the html; there should be
        # two ###. a string would be of the form '###firstpart###secondpart' which says where the data
        # is located.
        if dict_paths[col][0:3] == '###':
            data_element = clean_str(str(misc_path(data_html, dict_paths[col])))
            dict_out[col].append( data_element )
        else:
            if not(is_path(dict_paths[col])):
                for i in range(0, num_locations):
                    dict_out[col].append(dict_paths[col])
            else:
                temp_list = tree.xpath(dict_paths[col])
                if len(temp_list) == 0:
                #       if not(is_path(dict_paths[col])):
                #   for i in range(0, num_locations):
                #       dict_out[col].append(dict_paths[col])
                #else:
                    for i in range(0, num_locations):
                        dict_out[col].append('na')
                else:
                    for el in temp_list:
                        dict_out[col].append(clean_str(str(el)))
    return dict_out

# parse the data between two strings using the convention ###firststring###secondstring
# this is useful, for example, when we have javascript or something weird appearing in the html / xml that isn't
# html / xml (by the way, what is xml?)
def misc_path(html_data, path_data):
    [str_bad, str0, str1] = path_data.split('###')
    nicetext = inbetween_text(html_data, str0, str1)
    return nicetext

# check to see if the string is a valid xpath (?) path
def is_path(str_path):
    if str_path[0:2] == '(.' or str_path[0:2] == './':
        return True
    else:
        return False

# return the text in string that is inbetween the substrings str1 and str2
def inbetween_text(string, str1, str2):
    # if there isn't anything there then return -1 as we haven't found anything.
    if (string.find(str1) == -1 or string.find(str2) == -1):
        return -1
    else:
        start = string.find(str1) + len(str1)
        end = string[start:].find(str2)
        return string[start:start+end]

# just remove the line breaks, new lines and tab spaces from the string.
def clean_str(string):
    return string.replace('\n','').replace('\r','').replace('\t','')

# function that will either find an xpath or special path(starting with ###) depending on the string given
def path_to_data(html_data, path_string):
    if path_string[0:3] == '###':
        gooddata = clean_str(str(misc_path(html_data, path_string)))
    else:
        tree = html.fromstring(bytes(html_data, 'utf-8'))
        gooddata = tree.xpath(path_string)
    return gooddata

# order the columns of the spreadsheet so that it looks nice. This doesn't really work anymore unless all of the
# column titles below appear in the data frame.
def nice_order(df):
    col_titles = ['Brand', 'Site Reference', 'Title', 'Address', 'Suburb', 'State',
                  'Postcode', 'Country', 'Latitude', 'Longitude', 'Phone']
        
    df_nice = df[col_titles]
    return df_nice

# get just the JSON part so we can parse it. This is pretty messy. Clean it up.
def get_json(text):
    # find either a '{"' or '[{' or '{' which is where the json starts (is this general enough for all cases?)
    start0, end0 = text.find('{"'), text.rfind('}')
    start1, end1 = text.find('[{'), text.rfind(']')
    start2, end2 = text.find('{'), text.rfind('}')
    # this looks crappy, find a more elegant way to do this
    minone = min(start0, start1, start2)
    if (minone == start0) & (minone != -1):
        return text[start0:end0+1]
    elif (minone == start1) & (minone != -1):
        return text[start1:end1+1]
    else:
        return text[start2:end2+1]

# takes a dictionary and a list of strings, which represent keys in the dictionary and descends through the 'tree'
# of the dictionary to get to the specified part of the dictionary
# E.g., if keys_list = ['a', 'b', 'c'] then the function will return dict_input['a']['b']['c']
# if the keys_list is a string that starts with '###' then it is special and we just return the text after it.
def dict_descent(dict_input, keys_list):
    # is there is no keys_list then we just return the input (i.e., we didn't have to move down into the dictionary)
    if keys_list == None:
        return dict_input
    # if the keys_list is a string then we just take that as the value we are looking up in the dictionary
    elif type(keys_list) is str:
        try:
            value = dict_input[keys_list]
            return value
        except KeyError:
            return keys_list
    # if the keys_list is a list then keep 'descending' into the dictionary to get the required data. Could do this recursively
    elif type(keys_list) is list:
        for key in keys_list:
            try:
                dict_input = dict_input[key]
            except KeyError:
                return 'Error: No such path in dictionary'
        return dict_input
    else:
        print("Invalid key list provided. Should be a single string, list or else empty")

class Scraper:
    def __init__(self, url_list, data_hier, http_verb, scrape_type, params=None, payload=None, headers=None, key=None, print_counter=False):
        self.data_hier = data_hier
        self.url_list = url_list
        self.http_verb = http_verb
        self.scrape_type = scrape_type
        self.params = params
        self.payload = payload
        self.headers = headers
        self.df = pd.DataFrame() # for storing the data
        self.key = key
        self.print_counter = print_counter
    
    def scrape(self):
        num_successes = 0
        if self.http_verb == 'GET':
            for url in self.url_list:
                page = requests.get(url=url, params=self.params, headers=self.headers)
                if page.status_code == 200:
                    self.data = page.text
                    df_temp = self.delimit(self.data)
                    self.df = self.df.append(df_temp).drop_duplicates()
                    num_successes += 1
                    if self.print_counter: print("Number: %d"%num_successes)
                else:
                    print("Error: %d"%page.status_code)
            print("Sucessfully scraped %d URLs and found %d locations"%(num_successes, self.df.shape[0]))
                  
        elif self.http_verb == 'POST':
            num_successes = 0
            for url in self.url_list:
                page = requests.post(url=url, params=self.params, json=self.payload, headers=self.headers)
                if page.status_code == 200:
                    self.data = page.text
                    df_temp = self.delimit(self.data)
                    self.df = self.df.append(df_temp).drop_duplicates()
                    num_successes += 1
                    if self.print_counter: print("Number: %d"%num_successes)
                else:
                  print("Error: %d"%page.status_code)
            print("Sucessfully scraped %d URLs and found %d locations"%(num_successes, self.df.shape[0]))
        else:
            print('Error: invalid http verb. Only "GET" and "POST" are valid')
                        
    def delimit(self, data):
        if self.scrape_type == 'JSON':
            df = pd.DataFrame(data = json_bundle(self.data, self.data_hier, self.key))
            return df
        elif self.scrape_type == 'HTML':
            df = pd.DataFrame(data = html_bundle(self.data, self.data_hier))
            return df
        else:
            print('Error: invalid scrape type. Must be either "JSON" or "HTML" ')
                        
    def get_data(self):
        return self.df

# chain scrapers together, the output of one being the input of the next
# scrapers is an arbitrary number of scrapers, pipes is an abritrary number of pipes (i.e., fields that link the scrapers) and there should be one less of these
# than the number of scrapers

# Idea: scrape data from the first scraper, collect the field pipes[0], use this the list of urls for the second scraper
# This won't be general enough at this stage, but should be able to handle multi-url scrapes well.
class Pipeline:
    def __init__(self, scrapers, links):
        if len(scrapers) != (len(pipes) + 1):
            print("Error: insufficient number of scrapers or pipes")
        else:
            for scrp in range(0, len(scrapers)):
                scraper1 = scrapers[i]
                scraper1.scrape()
                data = scraper1.get_data()
                outs = data[pipes[i]].values()
                scraper[i+1].url_list = outs
