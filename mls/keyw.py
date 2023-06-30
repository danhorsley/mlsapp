import requests
import json
from decouple import config
import spacy

def get_keywords_from_isbn(isbn_list):
    #this uses google api to get information for each ISBN and can use up to 100k times a day (more maybe)
    base_url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
    #api_key = config('google_api_key')
    keywords_dict = {}

    for isbn in isbn_list:
        full_url = base_url + isbn
        response = requests.get(full_url)
        data = json.loads(response.text)
        
        if "items" in data:  # if the book was found
            book_info = data["items"][0]  # take the first found book
            #if "volumeInfo" in book_info and "categories" in book_info["volumeInfo"]:
                #keywords_dict[isbn] = book_info["volumeInfo"]["categories"]
            if "volumeInfo" in book_info and "description" in book_info["volumeInfo"]:
                keywords_dict[isbn] = book_info["volumeInfo"]["description"]

    return keywords_dict

def extract_named_entities(text):
    #extracts named entities from a given text (i.e. a book description)
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    named_entities = [ent.text for ent in doc.ents if ent.label_ != 'CARDINAL' and ent.label_ != 'ORDINAL']
    return named_entities


def filter_keywords(named_entities, trending_keywords):
    #filters out from list any trendign keywords so I can highlight books that match
    filtered_keywords = []
    for entity in named_entities:
        for keyword in trending_keywords:
            if keyword.lower() in entity.lower():
                filtered_keywords.append(entity)
                break
    return filtered_keywords