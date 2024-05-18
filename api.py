import requests
import pandas as pd
import folium
from math import radians, sin, cos, sqrt, atan2

API_KEY = '8XG6nkkP4BsPDIcto1VKdGUS3AAzrEvx'  

def get_route_info(start_lat, start_lng, end_lat, end_lng, api_key):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lng}:{end_lat},{end_lng}/json?key={api_key}&routeType=fastest&traffic=true&maxAlternatives=4"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Received status code {response.status_code}")
        print(response.text)
        return None

def parse_route_data(route_data, start_lat, start_lng, end_lat, end_lng):
    routes = []
    for route in route_data['routes']:
        route_segments = []
        for leg in route['legs']:
            for point in leg['points']:
                route_segments.append({
                    'latitude': point['latitude'],
                    'longitude': point['longitude']
                })
        total_distance = calculate_manual_total_distance(route_segments)
        deviation = compare_by_deviation(route_segments, start_lat, start_lng, end_lat, end_lng)
        print(deviation)
        traffic_delay = route['summary']['trafficDelayInSeconds']
        total_time = route['summary']['travelTimeInSeconds'] + traffic_delay
        avg_speed_kmh = (total_distance / total_time) * 3.6 if total_time > 0 else 0

        for segment in route_segments:
            segment['speed'] = avg_speed_kmh

        routes.append({
            'summary': route['summary'],
            'segments': route_segments,
            'total_time': avg_speed_kmh,
            'deviation': deviation
        })
    return routes

def compare_by_deviation(route_segments, start_lat, start_lng, end_lat, end_lng):
    main_path_tan = (end_lat - start_lat) / (end_lng - start_lng)
    main_path_b = end_lat - main_path_tan * end_lng
    tot = 0

    for point in route_segments:
        point_y = point['latitude']
        point_x = point['longitude']
        tot += abs(main_path_tan * point_x - point_y + main_path_b) / sqrt(main_path_tan**2 + 1)

    return tot / len(route_segments) * 111

def compare_routes_time(start_lat, start_lng, end_lat, end_lng, api_key):
    route_data = get_route_info(start_lat, start_lng, end_lat, end_lng, api_key)
    if route_data:
        routes = parse_route_data(route_data, start_lat, start_lng, end_lat, end_lng)
        routes.sort(key=lambda x: x['total_time'])
        return routes
    else:
        print("No route data available")
        return None

def compare_routes_deviation(start_lat, start_lng, end_lat, end_lng, api_key):
    route_data = get_route_info(start_lat, start_lng, end_lat, end_lng, api_key)
    if route_data:
        routes = parse_route_data(route_data, start_lat, start_lng, end_lat, end_lng)
        routes.sort(key=lambda x: x['deviation'])
        routes = routes[::-1]
        return routes
    else:
        print("No route data available")
        return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def calculate_manual_total_distance(route_segments):
    total_distance = 0.0
    for i in range(1, len(route_segments)):
        point1 = route_segments[i - 1]
        point2 = route_segments[i]
        distance = haversine(point1['latitude'], point1['longitude'], point2['latitude'], point2['longitude'])
        total_distance += distance
    return total_distance

def create_map(routes):
    if not routes or len(routes) < 2:
        print("Not enough routes to display")
        return None
    
    map_route = folium.Map(location=[routes[0]['segments'][0]['latitude'], routes[0]['segments'][0]['longitude']], zoom_start=13)
    colors = ['green', 'gray', 'blue', 'red', 'purple']
    
    for i, route in enumerate(routes[:3]):
        color = colors[i % len(colors)]
        route_df = pd.DataFrame(route['segments'])
        folium.PolyLine(route_df[['latitude', 'longitude']].values, color=color, weight=5, opacity=0.7).add_to(map_route)
        
        
        folium.Marker(
            location=[route_df.iloc[0]['latitude'], route_df.iloc[0]['longitude']],
            popup=(f"Total Distance (API): {route['summary']['lengthInMeters'] / 1000:.2f} km\n"
                   f"Travel Time: {route['summary']['travelTimeInSeconds'] / 60:.2f} mins\n"
                   f"Traffic Delay: {route['summary']['trafficDelayInSeconds'] / 60:.2f} mins\n"
                   f"Average Speed: {route_df['speed'].iloc[0]:.2f} km/h"),
            icon=folium.Icon(color=color)
        ).add_to(map_route)
    
    return map_route


start_lat = 41.013503273814344
start_lng = 29.03877220976081
end_lat = 41.152611018576444
end_lng = 28.864401400624395


routes = compare_routes_time(start_lat, start_lng, end_lat, end_lng, API_KEY)
routes2 = compare_routes_deviation(start_lat, start_lng, end_lat, end_lng, API_KEY)

route_map = create_map(routes)
route_map2 = create_map(routes2)
if route_map:
    route_map.save('map.html')
    route_map2.save('map2.html')
else:
    print("Failed to create route map")
