# Import necessary libraries
import openai
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
 
# Get the first command line argument
location = sys.argv[1]
sku = sys.argv[2]

# Initialize an empty dictionary for credentials
credentials = {}

# Define the file path to the credentials file
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
            f"Use them to come up with a new name that is max 70 chars long and will rank well with regard to SEO. If there is a mention of price. Change it to some other descriptive language."
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
                "content": f"I have an image with the name '{image_name}'. Please suggest a new name for the image."
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

def generate(new_pics_prompt):
    res = openai.Image.create(
        prompt=new_pics_prompt,
        n=1,
        size="256x256",
    )
    return res["data"][0]["url"]

def add_watermark(image_url, watermark_text):
    try:
        # Download the image from the URL
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Open the downloaded image using PIL
        image = Image.open(response.raw)

        # Create a drawing object for the image
        draw = ImageDraw.Draw(image)

        # Define the font and size for the watermark
        font = ImageFont.truetype('path_to_font.ttf', size=40)

        # Calculate the width and height of the watermark text
        text_width, text_height = draw.textsize(watermark_text, font=font)

        # Calculate the position to place the watermark text (centered on the image)
        image_width, image_height = image.size
        x = (image_width - text_width) // 2
        y = (image_height - text_height) // 2

        # Apply the watermark by drawing the text on the image
        draw.text((x, y), text=watermark_text, font=font, fill=(255, 255, 255, 128))

        # Save the modified image (you can overwrite the original file or save to a new file)
        image.save('path_to_save_image.jpg')
        
    except Exception as e:
        print(f"Error adding watermark to image: {str(e)}")

locations = []

# Open the credentials file
with open(creds_file_path) as f:
    # Initialize variables for parsing the file
    website = None
    user = None
    city = None
    phone = None
    consumer_key = None
    consumer_secret = None
    openai.api_key = None
    # pdb.set_trace()
    for line in f:
        # pdb.set_trace()
        line = line.strip()  # Remove trailing and leading whitespace
        # pdb.set_trace()
        if line.startswith("[") and line.endswith("]"):
            # pdb.set_trace()
            if website and user and city and phone and consumer_key and consumer_secret and openai.api_key:
                # pdb.set_trace()
                locations.append(Location(website, user, city, phone, consumer_key, consumer_secret, openai.api_key))
                # pdb.set_trace()
            website = line[1:-1].lstrip()  # Remove the brackets and any leading whitespace
            # pdb.set_trace()
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
        
#fetches the first product dataset to be edited and pushed to the other sites.
for locationa in locations:
    base_url = "https://" + locationa.website + "/wp-json/wc/v3/products"
    consumer_key = locationa.website + "_consumer_key:" + locationa.consumer_key
    consumer_secret = locationa.website + "_consumer_secret:" + locationa.consumer_secret
    city = locationa.city
    phone = locationa.phone
    website = locationa.website
    aikey = openai.api_key

    auth = (
        locationa.consumer_key,
        locationa.consumer_secret,
    )

    response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
    response.raise_for_status()

    product = response.json()[0]
    source_product = product
    source_product['images'] = remove_keys(source_product['images'])

    source_product_name = product['name'].strip()
    print("Source Product\n",source_product_name)
    print(website, aikey)
    print()
    source_images = source_product['images'][:4]  
    print("Source Images")
    print()
    imgcnt = 0
    for item in source_images:
        imgcnt = imgcnt + 1
        itemname = item['name'].replace('-',' ').capitalize()
        print("Image #", imgcnt)
        if  "Screen" in itemname:
            print("*", itemname)
        else:
            print(itemname)
        itemurl = item['src']        
        print(itemurl)
    break

# new_product_name = generate_new_product_name(sku)
# print("New name suggestion:", new_product_name)

seq = 0
#fetches all but the first product and applies the updated first site product details.
print("Destination Products\n")
for locationb in locations[1:]:
    seq = seq + 1
    base_url = "https://" + locationb.website + "/wp-json/wc/v3/products"
    consumer_key = locationb.website + "_consumer_key:" + locationb.consumer_key
    consumer_secret = locationb.website + "_consumer_secret:" + locationb.consumer_secret
    city = locationb.city
    city = city.replace('"', '')
    phone = locationb.phone
    phone = phone.replace(' ', '').replace('-', '').replace('"', '').replace('(', '').replace(')', '')

    website = locationb.website
    aikey = openai.api_key

    auth = (
        locationb.consumer_key,
        locationb.consumer_secret,
    )

    response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
    response.raise_for_status()

    product = response.json()[0]
    #source_product = product
    source_product['images'] = remove_keys(source_product['images'])
    print()
    msgg = "#" + str(seq) + " " + str(sku)
    print(msgg)
    subdomain = website.split('.')[0]
    print("Domain: ", subdomain)
    print(city, "Doap")
    print(city, " Ca ", phone)
    print("Sku: ", sku)
    print()
    print("Dest product name")
    # First AI call: generate new product name
    # product['name'] = generate_new_product_name(sku).replace('"','')
    print(product['name'])
    print()
    print("Images")
    print()
    imgcnt = 0
    for item in source_images:
        imgcnt = imgcnt + 1
        itemname = item['name'].replace('-',' ').capitalize()
        print("Image #", imgcnt)
        if  "Screen" in itemname:
            new_unique_product_name = generate_new_image_name(source_product['name']).replace('"','')
            print("*", new_unique_product_name)
            # print("*", itemname)
        else:
            # Second. A batch of AI calls that generate new product image names.
            new_unique_product_name = generate_new_image_name(itemname).replace('"','')
            item['name'] = new_unique_product_name 
            # print(itemname)
            print(new_unique_product_name)
        itemurl = item['src']        
        print(itemurl)
    #pprint.pprint(source_images)
    break

