import sys
import json
import os
import nltk
import requests
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


websites = []

with open(creds_file_path) as f:
    current_section = None
    for line in f:
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            websites.append(current_section)  # add websites to list
        elif current_section is not None:  # ensures not storing of siteless data
            key, value = line.split("=")
            credentials[current_section.split(".")[0] + "_" + key.strip()] = value.strip()

for website in websites:
    auth = (
        credentials[website.split(".")[0] + "_consumer_key"],
        credentials[website.split(".")[0] + "_consumer_secret"]
    )

    base_url = "https://" + website + "/wp-json/wc/v3/products"

    response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
    response.raise_for_status()

    if not response.json():
        print(f"No product found with SKU: {sku} on website: {website}")
        continue

    product = response.json()[0]

    with open('product.json', 'a') as json_file:   # use 'a' for append
        json_file.write(json.dumps(product) + "\n")  # write each product as a new line

    old_product_name = product['name']

    image_count = 0
    for image in product['images']:
        image_count = image_count + 1
    pprint.pprint(product)
    print("Image count", image_count)
    print()
    print()
    print("Next site...")
