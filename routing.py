import geopy
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import osmnx as ox
import taxicab as tc
import matplotlib.pyplot as plt
import numpy as np
import math

class Routing:
    def find_vectors(self, path_nodes):
        node_coords = []
        vector_list = []
        # Extract coordinates from each node on path
        for index, row in path_nodes.iterrows():
            node_coords.append((row['geometry'].y, row['geometry'].x))  # Append (longitude, latitude) tuple
        # loop through list of coordinates and calculate vectors
        for i in range(0, len(node_coords)-1): 
            vector_list.append((node_coords[i+1][0]-node_coords[i][0], node_coords[i+1][1]-node_coords[i][1]))
        return vector_list

    # Detta är ganska bra på att hitta skarpa kurvor, men inte jätteanvändbart för mer utdragna kurvor
    # kan kanske rödljusigenkänning göra samma sak?

    def calculate_angles(self, vectors):
        for i in range(0, len(vectors)-1):
            dotproduct = np.dot(vectors[i+1],vectors[i])
            length_v1 = np.linalg.norm(vectors[i])
            length_v2 = np.linalg.norm(vectors[i+1])
            product = abs(dotproduct)/(length_v1*length_v2)
            theta = math.acos(product)*180/math.pi
            print("Kurva nummer: ",i+1," Vinkel: ",theta)
            #if theta >= 0:
            #    print("Kurva nummer: ",i+1," Vinkel: ",theta)

    def route(self, address1, address2):
        # Geocode addresses to get coordinates
        geolocator = geopy.Nominatim(user_agent="my_geocoder")
        location1 = geolocator.geocode(address1)
        location2 = geolocator.geocode(address2)
        point1 = (location1.latitude, location1.longitude)
        point2 = (location2.latitude, location2.longitude)

        # Get street network graph for the surrounding area
        G = ox.graph_from_point(point1, dist=2500, network_type="drive")
        nodes, edges = ox.graph_to_gdfs(G)
        nodes.head()

        # Use taxicab to find the shortest path between points
        route = tc.distance.shortest_path(G, point1, point2)

        path_nodes = nodes.loc[route[1]]

        vectors = self.find_vectors(path_nodes)
        self.calculate_angles(vectors)

        fig, ax = ox.plot_graph_route(G, route[1], route_linewidth=1, show=False, close=False)
        path_nodes.plot(ax=ax, color='red', markersize=15)
        plt.show()
