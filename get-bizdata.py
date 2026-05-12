import googlemaps
import json
import geopy.distance
import time
import requests 

# Variables 
api_key = "{redacted here}"
final_results = {}

valid_place_types = [
    "accounting",
    "aquarium", 
    "book_store", 
    "car_dealer", 
    "casino", 
    "dentist", 
    "doctor", 
    "electrician", 
    "funeral_home",
    "gym", 
    "hardware_store", 
    "insurance_agency", 
    "jewelry_store", 
    "lawyer", 
    "liquor_store", 
    "locksmith", 
    "lodging", 
    "movie_theater", 
    "moving_company", 
    "painter", 
    "physiotherapist", 
    "plumber", 
    "real_estate_agency", 
    "roofing_contractor", 
    "spa", 
    "stadium", 
    "storage", 
    "store", 
    "supermarket",
    "university",
    "veterinary_care",
    "zoo"
]
attributes_to_delete = [
    "business_status",
    "curbside_pickup", 
    "current_opening_hours", 
    "delivery", 
    "dine_in", 
    "editorial_summary",
    "icon", 
    "icon_background_color", 
    "icon_mask_base_uri", 
    "international_phone_number", 
    "opening_hours", 
    "permanently_closed", 
    "photos", 
    "plus_code",
    "price_level", 
    "rating", 
    "reference",
    "reservable",  
    "reviews", 
    "scope", 
    "secondary_opening_hours", 
    "serves_beer", 
    "serves_breakfast", 
    "serves_brunch", 
    "serves_dinner", 
    "serves_lunch", 
    "serves_vegetarian_food", 
    "serves_wine", 
    "takeout", 
    "user_ratings_total", 
    "utc_offset", 
    "wheelchair_accessible_entrance"
]
corporate_types = [
    "bank", 
    "convenience_store",
    "drugstore",
    "gas_station"
]

# Company location
class CompanyLocation:
    def __init__(self, lat_num, lng_num, output_file, radius, pins = []): 
        self.latlng_str = str(lat_num) + ", " + str(lng_num)
        self.lat_num = lat_num
        self.lng_num = lng_num
        self.output_file = output_file
        self.radius = radius                    # miles
        self.pins = pins

# Populate alternate pins for query
def generate_pins(company_loc, square_side_m):
    deg_per_m = 0.05625
    radius = company_loc.radius

    x = company_loc.lat_num
    y = company_loc.lng_num
    s = square_side_m * deg_per_m
    n =  int(radius / square_side_m)

    # print("n: ", n)

    pins = [company_loc.latlng_str]

    for i_y in range(2*n):
        for i_x in range(2*n):
            
            new_x = x + (s*(1+2*i_x-2*n))/2
            new_y = y + (s*(2*n-2*i_y-1))/2

            new_coord_as_str = str(new_x) + ", " + str(new_y)
            pins.append(new_coord_as_str)
    
    company_loc.pins = pins

# Query Google Maps API for locations of a given type
def query_google_places(pin, type, next_page_token): 
    gmaps = googlemaps.Client(key=api_key)
    # print("Accessed Google API")

    response = gmaps.places(
        location = pin,
        language = "English", 
        type = type, 
        page_token = next_page_token
    )

    return(response)

# Clean and store raw Google Maps locations data 
def clean_raw_place_results(location, raw_results): 
    
    global final_results

    loc_count = 0 
    dup_count = 0
    closed_count = 0
    far_count = 0

    for loc in raw_results:

        # Reject duplicates from earlier pin queries
        if loc["place_id"] in final_results: 
            dup_count += 1
            # print("Rejected duplicate location: ", loc["name"], ", ", loc["place_id"])
            continue

        # Reject permanently closed businesses
        if "business_status" in loc:
            if loc["business_status"] != "OPERATIONAL":
                closed_count += 1
                # print("Rejected closed location")
                continue
        
        # Simplify location's geometry info
        loc_lat = loc["geometry"]["location"]["lat"]
        loc_lng = loc["geometry"]["location"]["lng"]
        del loc["geometry"]
        loc["lat"] = loc_lat
        loc["lng"] = loc_lng

        # Add distance from company
        coords1 = (location.lat_num, location.lng_num)
        coords2 = (loc["lat"], loc["lng"])
        distance = geopy.distance.distance(coords1, coords2).miles
        loc["distance_to_loc"] = distance 

        # Reject businesses that are too far away
        if distance > location.radius: 
            far_count += 1
            # print("Rejected location outside of the search radius:", str(distance), "miles away")
            continue 

        # Delete extra attributes
        for attribute in attributes_to_delete:
            if attribute in loc: 
                del loc[attribute]

        # Simplify location type
        loc_type = loc["types"][0]
        del loc["types"]
        loc["type"] = loc_type

        # Store cleaned location
        # print("Recorded location:", loc["name"], ", ", loc["place_id"])
        final_results[loc["place_id"]] = loc

        loc_count += 1
    
    print("Stored ", str(loc_count), " locations")
    print("Rejected:")
    print(" - ", str(closed_count), " permanently closed")
    print(" - ", str(dup_count), " duplicates")
    print(" - ", str(far_count), " outside search radius")

# Clean unwanted types from final results JSON
def purge_invalid_types(original_file, new_file):
    with open(original_file) as f: 
        data = json.load(f)

    print("Total number of locations: ", len(list(data)))
    del_count = 0

    for loc in list(data):
        if data[loc]["type"] not in valid_place_types: 
            print("Deleted location: ", data[loc]["name"], ", ", data[loc]["type"])
            del_count += 1 
            del data[loc]

    print("Updated number of locations: ", len(list(data)))
    print("Number of deleted locations: ", del_count)

    with open(new_file, "w") as f: 
        json.dump(data, f) 

def purge_invalid_corporate_types(original_file, new_file):
    with open(original_file) as f: 
        data = json.load(f)

    print("Total number of locations: ", len(list(data)))
    del_count = 0

    for loc in list(data):
        if data[loc]["type"] not in corporate_types: 
            print("Deleted location: ", data[loc]["name"], ", ", data[loc]["type"])
            del_count += 1 
            del data[loc]

    print("Updated number of locations: ", len(list(data)))
    print("Number of deleted locations: ", del_count)

    with open(new_file, "w") as f: 
        json.dump(data, f) 

# Update JSON with new data
def update_json(file, new_data):

    with open(file) as f: 
        data = json.load(f)

    data.update(new_data)

    with open(file, "w") as f: 
        json.dump(data, f) 
    
# Generate database from Google Maps
def create_database(location):
    
    global final_results

    print("Starting data build...")
    print("")
    print("Number of pins to query:", str(len(location.pins)))
     
    pin_count = 1

    # Query Google + store results for each preferred type
    
    for pin in location.pins: 

        print("")
        print("-----------------------------------")
        print("NEW PIN: ", str(pin))
        print("#", str(pin_count), " of ", str(len(location.pins)), " pins")

        for t in valid_place_types: 
            print("")
            print("TYPE: ", str(t))
            print("")

            page_count = 1 
            next_page = ""
        
            while next_page != None:
                
                # Pause to let next page token initialize
                if page_count > 1: 
                    # print("Pausing...")
                    print("")
                    time.sleep(2)

                # Query Google Maps API for locations
                print("Pulling page ", str(page_count), " of results...")
                response = query_google_places(pin, t, next_page)

                # Store raw locations and next page token
                temp_results = response["results"] 
                if "next_page_token" in response: 
                    next_page = response["next_page_token"]
                    # print("Next page token logged")
                else: 
                    next_page = None 

                # Edit raw results and store in a new dictionary
                clean_raw_place_results(location, temp_results)
                
                page_count += 1 
        
        update_json(location.output_file, final_results)
        pin_count +=1

    # Store response in JSON
    # print("Compiling final JSON file...")
    # with open(location.output_file, "w") as f:
    #     json.dump(final_results, f)

    print("All done!")

def create_corporate_database(location, output_file):
    
    global final_results

    print("Starting data build...")
    print("")
    print("Number of pins to query:", str(len(location.pins)))
     
    pin_count = 1

    # Query Google + store results for each preferred type
    
    for pin in location.pins: 

        print("")
        print("-----------------------------------")
        print("NEW PIN: ", str(pin))
        print("#", str(pin_count), " of ", str(len(location.pins)), " pins")

        for t in corporate_types: 
            print("")
            print("TYPE: ", str(t))
            print("")

            page_count = 1 
            next_page = ""
        
            while next_page != None:
                
                # Pause to let next page token initialize
                if page_count > 1: 
                    # print("Pausing...")
                    print("")
                    time.sleep(2)

                # Query Google Maps API for locations
                print("Pulling page ", str(page_count), " of results...")
                response = query_google_places(pin, t, next_page)

                # Store raw locations and next page token
                temp_results = response["results"] 
                if "next_page_token" in response: 
                    next_page = response["next_page_token"]
                    # print("Next page token logged")
                else: 
                    next_page = None 

                # Edit raw results and store in a new dictionary
                clean_raw_place_results(location, temp_results)
                
                page_count += 1 
        
        update_json(output_file, final_results)
        pin_count +=1

    print("All done!")

# Add website URLs to database
def add_urls(file):
    with open(file) as f: 
        data = json.load(f)

    loc_total = len(list(data))
    print("Total locations to query: ", loc_total)

    current_count = 0 

    for loc in data: 
        
        gmaps = googlemaps.Client(key=api_key)
        response = gmaps.place(
            place_id = loc, 
            fields = ["website"], 
            language = "English"
        )

        if response["result"] == {}:
            data[loc]["website"] = "None available"
        else: 
            data[loc]["website"] = response["result"]["website"]

        current_count += 1 
        remaining = loc_total - current_count
        print("Added URL — ", remaining, " remaining")

    with open(file, "w") as f: 
        json.dump(data, f) 

# Functions to fix errors for specific locations/queries
def add_urls_for_specificloc(file):
    with open(file) as f: 
        data = json.load(f)

    loc_total = len(list(data))
    print("Total locations to query: ", loc_total)

    current_count = 0 
    
    for loc in data: 
        if "website" not in data[loc]: 

            print("Querying for ID: ", loc, " (#", current_count, ")")

            gmaps = googlemaps.Client(key=api_key)
            response = gmaps.place(
                place_id = loc, 
                fields = ["website"], 
                language = "English"
            )

            if response["result"] == {}:
                data[loc]["website"] = "None available"
            else: 
                data[loc]["website"] = response["result"]["website"]

            current_count += 1 
            remaining = loc_total - current_count
            print("Added URL - ", remaining, " remaining")

            if current_count % 30 == 0: 
                with open(file, "w") as f: 
                    json.dump(data, f) 

    with open(file, "w") as f: 
        json.dump(data, f) 

def clean_queried_urls(file):
    with open(file) as f: 
        data = json.load(f)

    loc_total = len(list(data))
    print("Total locations to fix: ", loc_total)

    current_count = 0 

    for loc in list(data): 
        if data[loc]["website"]["result"] == {}:
            data[loc]["website"] = "None available"
        else: 
            url = data[loc]["website"]["result"]["website"]
            data[loc]["website"] = url

        # print(data[loc])

        current_count += 1 
        remaining = loc_total - current_count
        print("Fixed URL — ", remaining, " remaining")

    with open(file, "w") as f: 
        json.dump(data, f) 

def check_for_duplicates(file):
    with open(file) as f: 
        data = json.load(f)

    ids = data.keys()
    print("Length: ", len(ids))
    
    myset = set(ids)
    print("Uniques: ", len(myset))

    if len(ids) != len(myset): 
        print("There are duplicates in this list")

def test_refresh_place_ID(place_id): 
    # Requires requests to be installed

    url=f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=place_id&key={redacted_API_key}"

    try:
        response = requests.get(url)
        if response.status_code == 200: 
            posts = response.json
            print("Successfully found place")
            return posts
        else: 
            print("Error: ", response.status_code)
            return None
        
    except requests.exceptions.RequestException as e:
            print('Error:', e)
            return None

def refresh_place_IDs(file): 
    with open(file) as f: 
        data = json.load(f)

    loc_total = len(list(data))
    print("Total IDs to verify: ", loc_total)

    for loc in data: 
        place_id = data[loc]["place_id"]
        url=f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=place_id&key={redacted_API_key}"

        try:
            response = requests.get(url)
            if response.status_code == 200: 
                data[loc]["place_id"] = response.json
                print("Location ", place_id, " verified")
            else: 
                print("Error: ", response.status_code)
                return None
            
        except requests.exceptions.RequestException as e:
                print('Error with :', place_id, ": ", e)
                return None

# ------------------------------------------------- 

# Run for anonymized location
# loc = CompanyLocation(
#     {lat},
#     {long},
#     "output-loc.json", 
#     15)
# generate_pins(loc, 5)
        
# create_database(loc)
# purge_invalid_types("output-loc.json", "output-loc-cleaned.json")
# add_urls("output-loc-cleaned.json")

# create_corporate_database(loc, "output-loc-corporate.json")
# purge_invalid_corporate_types("output-loc-corporate.json", "output-loc-corporate-cleaned.json")

# ----------------------------------------

# FIXING ERRORS FOR SPECIFIC FILES

# for i in range(10):
#     loc1.pins.pop(0)

# clean_queried_urls("output-loc2-cleaned.json")
# add_urls_for_specificloc("output-loc3-cleaned.json")

# ----------------------------------------

# def test_add_urls(loc): 
#     gmaps = googlemaps.Client(key=api_key)
#     response = gmaps.place(
#         place_id = loc,
#         fields = ["website"], 
#         language = "English"
#     )
#     print(response)
# test_add_urls("ChIJRWNtzG0NK4cRNuedAHmRJg8")

# ----------------------------------------

# posts = test_refresh_place_ID("ChIJGSewKtp61oYRsXRZSe_yFis")
# refresh_place_IDs("output-loc4-cleaned.json")
