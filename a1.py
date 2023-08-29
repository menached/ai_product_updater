import openai
import subprocess
import sys
import json
import html
import re
import ssl
import os
import math
import glob
import pprint
import nltk
import pdb
import requests
import time
import random
from PIL import Image, ImageDraw, ImageFont
from PIL import UnidentifiedImageError
if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt', quiet=True)

sitelist = [
  { "subdomain": "alamo", "site_id": 29 },
  { "subdomain": "burlingame", "site_id": 30 },
  { "subdomain": "campbell", "site_id": 7 },
  { "subdomain": "castrovalley", "site_id": 25 },
  { "subdomain": "concord", "site_id": 31 },
  { "subdomain": "danville", "site_id": 9 },
  { "subdomain": "dublin", "site_id": 8 },
  { "subdomain": "hillsborough", "site_id": 12 },
  { "subdomain": "lafayette", "site_id": 13 },
  { "subdomain": "livermore", "site_id": 14 },
  { "subdomain": "orinda", "site_id": 34 },
  { "subdomain": "pittsburg", "site_id": 28 },
  { "subdomain": "pleasanthill", "site_id": 35 },
  { "subdomain": "sanramon", "site_id": 33 },
  { "subdomain": "walnutcreek", "site_id": 32 }
]

def get_site_id(subdomain):
  for site in sitelist:
    if site["subdomain"] == subdomain:
      return site["site_id"]
  return None

location = sys.argv[1]
sku = sys.argv[2]

credentials = {}

creds_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # Get the directory of the current file
    "../creds2.txt"  # Append the relative path to the credentials file
)
if os.path.exists('product.json'):
    os.remove('product.json')

class Location:
    def __init__(self, website, user, city, phone, consumer_key, consumer_secret, api_key):
        self.website = website
        self.user = user
        self.city = city
        self.phone = phone
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_key = api_key  # Here's the new attribute

def scp_file_to_remote(local_file, remote_file):
    try:
        # Run SCP command
        subprocess.Popen(["scp", local_file, remote_file])
        print("File transfer initiated.")
        
    except Exception as e:
        print("Error while copying the file:", e)

def download_image(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Image downloaded successfully: {filename}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {str(e)}")

def add_watermark_and_save(image_path, watermark_text, output_path):
    try:    
        image = Image.open(image_path).convert("RGBA")
        font = ImageFont.truetype("font.ttf", 40)
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        text_width, text_height = draw.textbbox((0, 0), watermark_text, font=font)[:2]
        position = (image.width - text_width - 10, image.height - text_height - 10) # Position the watermark in the lower right corner
        draw.text(position, watermark_text, font=font, fill=(128, 128, 128, 128))
        watermarked = Image.alpha_composite(image, overlay)
        watermarked.save(output_path)
        print(f"Watermarked image saved as {output_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

def makeunique(new_unique_product_name):
    ai_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful budtender who knows all about the cannabis industry.",
            },
            {
                "role": "user",
                "content": f"Use this product name '{new_unique_product_name}'. Use this phrase to come up with a slightly different name that means the same thing."
            f"Come up with a new name that is max 70 chars long and will rank well with regard to SEO. If there is a mention of price. Change it to some other descriptive language instead."
            },
        ]
    )

def generate_new_product_name(sku):
    ai_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful budtender who knows all about the cannabis industry.",
            },
            {
                "role": "user",
                "content": f"Use this product slug '{product['slug']}' to rewrite the product title. The slug contains words separated by a -."
            f"Use them to come up with a new name that is max 70 chars long and will rank well with regard to SEO. If there is a mention of price. Change it to some other descriptive language. Dont put spaces in the names. Use underscores to separate words."
            },
        ]
    )
    new_product_name = ai_response['choices'][0]['message']['content'].strip()
    new_product_name = html.unescape(re.sub('<.*?>', '', new_product_name))
    return new_product_name

def generate_new_image_name(image_name):
    ai_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a creative AI assistant and California Budtender for a delivery service.",
            },
            {
                "role": "user",
                "content": f"I have an image with the name '{image_name}'. Please suggest a new name for the image that does not use dates or times in the name. Limit the name to 70 characters. Dont put spaces in the names. Use underscores to separate words."
            },
        ]
    )

    new_image_name = ai_response['choices'][0]['message']['content'].strip()
    new_image_name = html.unescape(re.sub('<.*?>', '', new_image_name))

    return new_image_name

def remove_keys(images_data):
    keys_to_remove = [
    'date_created',
    'date_created_gmt',
    'date_modified',
    'date_modified_gmt',
    'id',
    'alt'
    ]   
    new_images_data = []
    for index, image_data in enumerate(images_data):
        if index < 4:
            new_image_data = {key: value for key, value in image_data.items() if key not in keys_to_remove}
        else:
            new_image_data = {}
        new_images_data.append(new_image_data)
    return new_images_data

locations = []

with open(creds_file_path) as f:
    website = None
    user = None
    city = None
    phone = None
    consumer_key = None
    consumer_secret = None
    openai.api_key = None
    for line in f:
        line = line.strip()  # Remove trailing and leading whitespace
        if line.startswith("[") and line.endswith("]"):
            if website and user and city and phone and consumer_key and consumer_secret and openai.api_key:
                locations.append(Location(website, user, city, phone, consumer_key, consumer_secret, openai.api_key))
            website = line[1:-1].lstrip()  # Remove the brackets and any leading whitespace
            user = None
            city = None
            phone = None
            consumer_key = None
            consumer_secret = None
            openai.api_key = None
        elif website and " = " in line:
            key, value = line.split(" = ")
            if key == "user":
                user = value
            elif key == "city":
                city = value
            elif key == "phone":
                phone = value
            elif key.lower().endswith("_consumer_key"):
                consumer_key = value
            elif key.lower().endswith("_consumer_secret"):
                consumer_secret = value
            elif key == "openai.api_key":
                openai.api_key = value
                aikey = value
            elif key == "website":
                website = value
     
    locations.append(
        Location(website, user, city, phone, consumer_key, 
                 consumer_secret, openai.api_key)
    )
        
for locationa in locations[:1]:
    base_url = "https://" + locationa.website + "/wp-json/wc/v3/products"
    consumer_key = locationa.website + "_consumer_key:" + locationa.consumer_key
    consumer_secret = locationa.website + "_consumer_secret:" + locationa.consumer_secret
    aikey = openai.api_key
    auth = (
        locationa.consumer_key,
        locationa.consumer_secret,
    )
    #city = locationa.city
    #phone = locationa.phone
    #website = locationa.website
    response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
    response.raise_for_status()
    product = response.json()[0]
    source_product = product
    source_product['images'] = remove_keys(source_product['images'])
    source_images = source_product['images'][:4]  
    imagecounter = 0
    for item in source_images:
        imagecounter = imagecounter + 1
        print("Image:",imagecounter, " src:", item['src'])

seq = 0
print("Destination Products\n")
for locationb in locations[1:]:
    seq = seq + 1
    base_url = "https://" + locationb.website + "/wp-json/wc/v3/products"
    consumer_key = locationb.website + "_consumer_key:" + locationb.consumer_key
    consumer_secret = locationb.website + "_consumer_secret:" + locationb.consumer_secret
    website = locationb.website
    subdomain = website.split('.')[0]
    site_id = get_site_id(subdomain)
    print("Site ID:", site_id) 
    aikey = openai.api_key
    auth = (
        locationb.consumer_key,
        locationb.consumer_secret,
    )
    response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
    response.raise_for_status()
    product = response.json()[0]
    product['images'] = source_product['images'] 
    msgg = "#" + str(seq) + " " + str(sku)
    print(msgg)
    while True:
        product_name = generate_new_product_name(sku).replace('"','').replace('"','').replace("'","").replace(" ","_").replace("(","").replace(")","").replace(",","").replace("$","")
        print("Is this new product name ok?: ", product_name)
        choice = input("Do you want to use this? [Y/N]: ")
        if choice.lower() == "y":
            product['name'] = product_name 
            break
        else:
            continue
    # to speed stuff up during dev
    del product['images'];

    print("Selected new product name: ", product['name'])

#print("New Images")
    imgcnt = 0
    for item in source_images:
        imgcnt = imgcnt + 1
        print("Image #", imgcnt)
    #break
#pprint.pprint(product)
pdb.set_trace()
update_url = f'{base_url}/{product["id"]}'
update_response = requests.put(update_url, json=product, auth=auth)
pdb.set_trace()
update_response.raise_for_status()
