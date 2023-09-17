from datetime import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import geopandas as gpd
import matplotlib.pyplot as plt
import osmnx as ox
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import math
import googlemaps
import pandas as pd
import time

app = Flask(__name__)
CORS(app)

gmaps = googlemaps.Client('AIzaSyBRFyET7UTLGn2lAm038hjp73wSF1KD0G8')

def generate_hexagonal_grid(boundary, hex_size):
    minx, miny, maxx, maxy = boundary.bounds
    dx = 3 / 2 * hex_size
    dy = math.sqrt(3) * hex_size

    hexagons = []

    # Calculate rows and cols
    rows = int((maxy - miny) / dy) + 1
    cols = int((maxx - minx) / dx) + 1

    for row in range(rows):
        for col in range(cols):
            x = minx + col * dx
            y = miny + row * dy

            # Stagger odd rows
            if col % 2 == 1:
                y += dy / 2

            # Create the vertices of the hexagon
            vertices = [(x + math.cos(math.radians(angle)) * hex_size,
                         y + math.sin(math.radians(angle)) * hex_size)
                        for angle in range(0, 360, 60)]

            hexagon = Polygon(vertices)
            hexagon = hexagon.intersection(boundary)

            if not hexagon.is_empty:
                hexagons.append(hexagon)

    return gpd.GeoDataFrame({'geometry': hexagons})

def process_hexagon(hexagon, keyword):

    final_results = set()

    if hexagon.geom_type == 'Polygon':
        polygons = [hexagon]
    elif hexagon.geom_type == 'MultiPolygon':
        polygons = hexagon.geoms

    for polygon in polygons:
        # Find the center of the polygon
        center = polygon.centroid
        center_lat, center_lng = center.y, center.x

        # Calculate the radius (distance from center to any vertex)
        vertex = polygon.exterior.coords[0]
        radius = center.distance(Point(vertex)) * 100000  # Convert from degrees to meters

        # Perform a nearby search using Google Maps API
        # keyword = 'REWE'  # Replace this with the keyword you're interested in
        places_result = gmaps.places_nearby(location=(center_lat, center_lng), radius=radius, keyword=keyword)

        # Process the places result
        for place in places_result.get('results', []):
            print(f"Found  {place.get('place_id')}")  # at {place.get('geometry', {}).get('location', {})}")
            final_results.add(place.get('place_id'))

        next_page_token = places_result.get('next_page_token')

        # Fetch additional results if a next_page_token is provided
        while next_page_token:
            time.sleep(5)  # Delay to allow the next_page_token to become valid
            places_result = gmaps.places_nearby(location=(center_lat, center_lng), radius=radius, keyword=keyword, page_token=next_page_token)
            for place in places_result.get('results', []):
                print(f"Found Additional:  {place.get('place_id')}")  # at {place.get('geometry', {}).get('location', {})}")
                final_results.add(place.get('place_id'))

            next_page_token = places_result.get('next_page_token')

    return final_results

def process_city_and_keyword(city_name, keyword):
    final_results = set()
    
    city = ox.geocode_to_gdf(city_name, which_result=1)
    boundary = unary_union(city.geometry)

    hex_size = 0.003  # This could be adjusted to your needs
    hex_grid = generate_hexagonal_grid(boundary, hex_size)

    for hexagon in hex_grid.geometry:
        hex_results = process_hexagon(hexagon, keyword)
        final_results.update(hex_results)

    return final_results

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html')

@app.route('/process_data', methods=['POST'])
def process_data():
    
    data = request.json
    city_name = data.get('city')
    keyword = data.get('keyword')

    if not city_name or not keyword:
        return jsonify({'error': 'Missing city_name or keyword'}), 400

    final_results = process_city_and_keyword(city_name, keyword)
    
    df = pd.DataFrame(columns=['No.', 'Name', 'Address', 'Telephone'])

    for idx, place_id in enumerate(final_results):
        place_result = gmaps.place(place_id=place_id)
        # print("Place result:", place_result)

        name = place_result["result"].get("name", 'N/A')
        address = place_result["result"].get("formatted_address", 'N/A')
        phone = place_result["result"].get("formatted_phone_number", 'N/A')

        new_row = pd.DataFrame({
            'No.': [idx + 1],
            'Name': [name],
            'Address': [address],
            'Telephone': [phone]
        })

        df = pd.concat([df, new_row]).reset_index(drop = True)

        time.sleep(5)
    # print(df)
    return jsonify(df.to_json(orient='split'))
    # return jsonify({"status": "success"})
if __name__ == "__main__":
    app.run(debug=True)