import requests
import pandas as pd
import folium

API_KEY = '8XG6nkkP4BsPDIcto1VKdGUS3AAzrEvx'  # Replace with your TomTom API key

def get_route_info(start_lat, start_lng, end_lat, end_lng, api_key):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lng}:{end_lat},{end_lng}/json?key={api_key}&routeType=fastest&traffic=true&maxAlternatives=1"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Received status code {response.status_code}")
        print(response.text)
        return None

def parse_route_data(route_data):
    routes = []
    for route in route_data['routes']:
        route_segments = []
        total_distance = route['summary']['lengthInMeters']
        
        traffic_delay = route['summary']['trafficDelayInSeconds']
        print(traffic_delay)
        total_time = route['summary']['travelTimeInSeconds'] + traffic_delay
        avg_speed_kmh = (total_distance / total_time) * 3.6 if total_time > 0 else 0

        for leg in route['legs']:
            for point in leg['points']:
                route_segments.append({
                    'latitude': point['latitude'],
                    'longitude': point['longitude'],
                    'speed': avg_speed_kmh
                })
        routes.append({
            'summary': route['summary'],
            'segments': route_segments,
            'total_distance': total_distance,
            'total_time': total_time,
            'traffic_delay': traffic_delay
        })
    return routes

def compare_routes(start_lat, start_lng, end_lat, end_lng, api_key):
    route_data = get_route_info(start_lat, start_lng, end_lat, end_lng, api_key)
    if route_data:
        routes = parse_route_data(route_data)
        routes.sort(key=lambda x: x['summary']['travelTimeInSeconds'])
        return routes
    else:
        print("No route data available")
        return None

def create_map(routes):
    if not routes or len(routes) < 2:
        print("Not enough routes to display")
        return None
    
    map_route = folium.Map(location=[routes[0]['segments'][0]['latitude'], routes[0]['segments'][0]['longitude']], zoom_start=13)
    colors = ['green', 'gray']
    
    for i, route in enumerate(routes[:2]):
        color = colors[i]
        route_df = pd.DataFrame(route['segments'])
        folium.PolyLine(route_df[['latitude', 'longitude']].values, color=color, weight=5, opacity=0.7).add_to(map_route)
        
        # Add route summary to the map
        folium.Marker(
            location=[route_df.iloc[0]['latitude'], route_df.iloc[0]['longitude']],
            popup=(f"Total Distance: {route['total_distance'] / 1000:.2f} km\n"
                   f"Travel Time: {route['total_time'] / 60:.2f} mins\n"
                   f"Traffic Delay: {route['traffic_delay'] / 60:.2f} mins\n"
                   f"Average Speed: {route_df['speed'].iloc[0]:.2f} km/h"),
            icon=folium.Icon(color=color)
        ).add_to(map_route)
    
    return map_route

# Example start and end coordinates
start_lat = 41.013503273814344
start_lng =  29.03877220976081
end_lat = 40.99608213805624
end_lng = 29.03373887879619

# Compare routes
routes = compare_routes(start_lat, start_lng, end_lat, end_lng, API_KEY)

route_map = create_map(routes)
if route_map:
    route_map.save('route_map2.html')
else:
    print("Failed to create route map")
