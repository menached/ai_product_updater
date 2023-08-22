# import openai
import sys
# import html
# import re
import json
import os
# import ssl
import nltk
import requests
# from PIL import Image
import pprint

if not nltk.data.find('tokenizers/punkt'):
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

auth = (
    credentials[location + "_consumer_key"],
    credentials[location + "_consumer_secret"]
)

base_url = "https://" + location + "/wp-json/wc/v3/products"

response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
response.raise_for_status()

if not response.json():
    print(f"No product found with SKU: {sku}")
    exit()

product = response.json()[0]

with open('product.json', 'w') as json_file:
    json.dump(product, json_file)

old_product_name = product['name']

image_count = 0
for image in product['images']:
    image_count = image_count + 1
pprint.pprint (product)
print("Image count", image_count)
print()
print()
print("Next site...")
