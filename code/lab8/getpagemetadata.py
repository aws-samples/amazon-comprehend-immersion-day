import os
import json
import boto3
import sys
from botocore.exceptions import ClientError

#Maximum number of strings in a STRING_LIST type attribute allowed by Kendra, default is 10, it can be increased on request
elimit = 10

#The minimum value we want to consider of the confidence score of recognized entity as returned by Comprehend Medical
min_score = 0.97

#Avoid exceeding Comprehend detect_entites API UTF 8 character limit
#compre_text_size = 3950
compre_text_size = 4000


client = boto3.client(service_name='comprehend')

#List of categories recognized by Comprehend Medical
categories = ["COMMERCIAL_ITEM", "DATE", "EVENT", "LOCATION", "ORGANIZATION", "OTHER", "PERSON", "QUANTITY", "TITLE"]


#The function to read a wikipedia page as a text file and detect entities in it using Medical Comprehend 
def document_handler(fname):
    doc_text = open(fname, 'r').read()
    #List of JSON objects to store entities
    entity_data = dict()
    #List of observed text strings recognized as categories
    category_text = dict()
    #Frequency of each text string
    text_frequency = dict()
    for et in categories:
        entity_data[ et ] = []
        category_text[ et ] = []
        text_frequency[ et ] = dict()
    #Make detect_entities_v2 call in a loop to work with the text limit
    #This splitting approach is likely a liitle too naive for a production application as it can potentially split entities,
    for i in range(0, len(doc_text), compre_text_size):
        try:
            entities = client.detect_entities(Text=doc_text[i:i+compre_text_size], LanguageCode='en')
        except Exception as e:
            print("Exiting - detect_entities terminated with exception", e, file=sys.stderr)
            sys.exit(1)
        for e in entities["Entities"]:
            #For each of the recognized entities take only those that have confidence score higher than min_score, 
            #are printable, dont contain quotes and are previously unseen
            if ((e["Score"] > min_score) and (e["Text"].isprintable()) and (not "\"" in e["Text"]) and (not e["Text"].upper() in category_text[e["Type"]])):
                #Append the text to entity data to be used for a Kendra custom attribute
                entity_data[e["Type"]].append(e["Text"])
                #Keep track of text in upper case so that we don't treat the same text written in different cases differently
                category_text[e["Type"]].append(e["Text"].upper())
                #Keep track of the frequency of the text so that we can take the text with highest frequency of occurrance
                text_frequency[e["Type"]][e["Text"].upper()] = 1
            elif (e["Text"].upper() in category_text[e["Type"]]):
                #Keep track of the frequency of the text so that we can take the text with highest frequency of occurrance
                text_frequency[e["Type"]][e["Text"].upper()] += 1
    #The Kendra attribute metadata JSON object to be populated
    attributes = dict()
    metadata = dict()
    for et in categories:
        metadata[et] = []
        #Take at most elimit number of recognized text strings having the highest frequency of occurrance
        el = [pair[0] for pair in sorted(text_frequency[et].items(), key=lambda item: item[1], reverse=True)][0:elimit]
        for d in entity_data[et]:
            if (d.upper() in el):
                metadata[et].append(d)
    #Use the input filename to determine the wikipedia page URL
    npfile = fname.split('.')[0]
    npname = npfile.split('/')[len(npfile.split('/')) - 1]
    npreplace = npname.replace("#", "/")
    metadata["_source_uri"] = "https://en.wikipedia.org/wiki/" + npreplace
    attributes["Attributes"] = metadata
    print(json.dumps(attributes, sort_keys=True, indent=4))

##main 
##The script takes the filename relative to local directory as input and outputs json to stdout
if (len(sys.argv) != 2):
    print("Usage: ", sys.argv[0], " <filename>\n");
    exit(1)
else:
    document_file = sys.argv[1]
    document_handler(document_file)
