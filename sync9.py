#fetches all but the first product and applies the updated first site product details.
for location in locations[1:]:
    base_url = "https://" + location.website + "/wp-json/wc/v3/products"
    consumer_key = location.website + "_consumer_key:" + location.consumer_key
    consumer_secret = location.website + "_consumer_secret:" + location.consumer_secret
    auth = (
        location.consumer_key,
        location.consumer_secret,
    )
    opkey = openai.api_key
    city = location.city
    phone = location.phone
    website = location.website

    response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
    response.raise_for_status()
    product = response.json()[0]
    product['name'] = "Super duper " + source_product['name']

    del product['date_created']
    del product['date_created_gmt']
    del product['date_modified']
    del product['date_modified_gmt']

    image_count = 0
    for image in product['images']:
        image_count = image_count + 1

    for image_index in range(image_count, 4):
        # Generate new image URL
        new_image_url = generate("Picture of a happy guy with a vape")

        # Check if the new image URL is already in new_images
        if new_image_url not in [image['src'] for image in product['images']]:
            # Append the new image URL to product['images']
            product['images'].append({'src': new_image_url, 'name': 'Happy guy with a vape.'})

    new_short_description = source_product['short_description'] + " Get 1hr delivery bo calling  " + city.strip('"') + " Doap at " + phone.strip('"') + " anytime between 9-9 daily 7 days a week. We deliver to " + city.strip('"') + " and surrounding cities!" 
    new_short_description = new_short_description.replace("Alamo", city.strip('"'))
    product['short_description'] = new_short_description.replace("925-553-4710", phone.strip('"'))

    new_description = source_product['description'] + " Get 1hr delivery bo calling  " + city.strip('"') + " Doap at " + phone.strip('"') + " anytime between 9-9 daily 7 days a week. We deliver to " + city.strip('"') + " and surrounding cities!" 
    new_description = new_description.replace("Alamo", city.strip('"'))
    #product['description'] = new_description
    product['description'] = new_description.replace("925-553-4710", phone.strip('"'))
    product['date_created'] = source_product['date_created']
    product['date_created_gmt'] = source_product['date_created_gmt']
    product['date_modified_gmt'] = source_product['date_modified_gmt']
    product['date_modified'] = source_product['date_modified']
    city = location.city
    phone = location.phone
    print("Processing: ",city)
    print("Setting source product title",product['name'], " on ", location.city)
    #print("Images: ",product['images'])
    print("City: ",city)
    #pprint.pprint(product)
    del product['date_created']
    update_url = f'{base_url}/{product["id"]}'
    update_response = requests.put(update_url, json=product, auth=auth)
    update_response.raise_for_status()
    images = product['images']
    images = images[:1]  # Keep only the first AI-generated image
    product['images'] = images
    pdb.set_trace()
    pprint.pprint(product)
