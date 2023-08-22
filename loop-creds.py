import openai
import sys
import json
import os
import nltk
import requests
import pdb; 
# pdb.set_trace()
if not nltk.data.find('tokenizers/punkt'):
    #breakpoint()
    nltk.download('punkt', quiet=True)

location = sys.argv[1] + ".doap.com"
sku = sys.argv[2]
credentials = {}

creds_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../creds2.txt"
)

with open(creds_file_path) as f:
    current_section = None
    for line in f:
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
        elif current_section == location:
            key, value = line.split(" = ")
            credentials[key] = value

openai.api_key = credentials["openai.api_key"]
city = credentials['city']
phone = credentials['phone']

auth = (
    credentials[location + "_consumer_key"],
    credentials[location + "_consumer_secret"]
)


print(
    f"Website: {location}\n"
    f"City: {city}\n"
    f"Phone: {phone}\n"
    f"OpenAI Key: {openai.api_key}\n\n"
)
