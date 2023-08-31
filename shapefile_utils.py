import geopandas as gpd
import pyproj
from shapely.geometry import box, Polygon
import random
from tqdm import tqdm
import folium
from folium.plugins import MarkerCluster
import multiprocessing

def create_rectangle_shapefile(lower_left, upper_right, crs='EPSG:4326'):
    # Create the rectangular geometry
    geometry = box(lower_left[0], lower_left[1], upper_right[0], upper_right[1])
    
    # Create a GeoDataFrame with the rectangular geometry
    return gpd.GeoDataFrame(geometry=[geometry], crs=crs)
    
def change_lat_with_lon(coords):
    return [(coord[1], coord[0]) for coord in coords]

def create_polygon(coords, crs='EPSG:4326'):
    # Create the rectangular geometry
    geometry = Polygon(coords)
    
    # Create a GeoDataFrame with the rectangular geometry
    return gpd.GeoDataFrame(geometry=[geometry], crs=crs)

def get_largest_geometry(geodf):
    # Calculate the area of each geometry in the GeoDataFrame
    geodf['area'] = geodf.geometry.area
    
    # Get the index of the geometry with the maximum area
    largest_index = geodf['area'].idxmax()
    
    # Get the largest geometry
    largest_geometry = geodf.loc[largest_index, 'geometry']
    
    return gpd.GeoDataFrame(geometry=[largest_geometry], crs=geodf.crs)

def intersect_shapefiles(shapefile1, shapefile2, crs):
    # Convert shapefiles to a common CRS
    shapefile1 = shapefile1.to_crs(crs)
    shapefile2 = shapefile2.to_crs(crs)
    
    # Perform the intersection
    return gpd.overlay(shapefile1, shapefile2, how='intersection')


def lat_lon_to_epsg(lat, lon, epsg):
    wgs84 = pyproj.CRS("EPSG:4326")  # WGS84 coordinate system (latitude and longitude)
    target_crs = pyproj.CRS(epsg)     # Target EPSG coordinate system
    
    transformer = pyproj.Transformer.from_crs(wgs84, target_crs, always_xy=True)
    transformed_point = transformer.transform(lon, lat)
    
    return transformed_point[0], transformed_point[1]

def generate_random_points_within_shapefile(shapefile, num_points, seed):
    
    # Set the seed for random number generation
    random.seed(seed)
    
    # Get the bounds of the shapefile
    xmin, ymin, xmax, ymax = shapefile.total_bounds
    
    # Generate random points within the bounds and ranges
    points = []
    with tqdm(total=num_points) as pbar:
        while len(points) < num_points:
            x = random.uniform(xmin, xmax)
            y = random.uniform(ymin, ymax)
            point = (x,y) # x -> lon, y-> lat
            
            # Check if the point is within the shapefile
            is_within = False
            for _, row in shapefile.iterrows():
                if row['geometry'].contains(gpd.points_from_xy([x], [y])[0]):
                    is_within = True
                    break
            
            if is_within:
                pbar.update(1)
                points.append(point)
    
    return points


def generate_random_points_within_shapefile_parallel(shapefile, num_points, seed):
    
    # Set the seed for random number generation
    random.seed(seed)
    
    # Get the bounds of the shapefile
    xmin, ymin, xmax, ymax = shapefile.total_bounds
    
    # Define a worker function for generating random points
    def generate_points_worker(num_points, xmin, xmax, ymin, ymax, progress_queue, result_queue, seed):
        # Set the seed for random number generation
        random.seed(seed)
        points = []
        while len(points) < num_points:
            x = random.uniform(xmin, xmax)
            y = random.uniform(ymin, ymax)
            point = (x, y)  # x -> lon, y -> lat
            
            # Check if the point is within the shapefile
            is_within = False
            for _, row in shapefile.iterrows():
                if row['geometry'].contains(gpd.points_from_xy([x], [y])[0]):
                    is_within = True
                    break
            
            if is_within:
                points.append(point)
        
        result_queue.put(points)
        progress_queue.put(num_points)
    
    # Create queues for tracking progress and collecting results
    progress_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    
    # Calculate the number of points for each worker
    num_workers = multiprocessing.cpu_count()
    points_per_worker = num_points // num_workers
    remaining_points = num_points % num_workers
    
    # Create and start worker processes
    processes = []
    for i in range(num_workers):
        worker_points = points_per_worker + (1 if i < remaining_points else 0)
        print("Worker {} will generate {} points".format(i, worker_points))
        process = multiprocessing.Process(
            target=generate_points_worker,
            args=(worker_points, xmin, xmax, ymin, ymax, progress_queue, result_queue, seed + i)
        )
        process.start()
        processes.append(process)
    
    # Create a progress bar
    with tqdm(total=num_points) as pbar:
        completed_points = 0
        
        # Wait for progress updates from worker processes
        while completed_points < num_points:
            completed_points += progress_queue.get()
            pbar.update(completed_points - pbar.n)
        
        # Collect results from worker processes
        points = []
        for _ in range(num_workers):
            worker_points = result_queue.get()
            points.extend(worker_points)
        
        # Terminate worker processes
        for process in processes:
            process.join()
    
    return points


def save_folium_map(latlon_pointsGDF, path, name):
    
    # Create a folium map centered around the mean coordinates of the points
    center_lat = latlon_pointsGDF['lat'].mean()
    center_lon = latlon_pointsGDF['lon'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
    for layer in ['stamentoner','stamenterrain', 'cartodbpositron', 'cartodbdark_matter', 'stamenwatercolor']:
        folium.TileLayer(layer).add_to(m)


    feature_group_b = folium.FeatureGroup("Locations blue")
    feature_group_y = folium.FeatureGroup("Locations yellow", show=False)
    for idx, row in latlon_pointsGDF.iterrows():
        feature_group_b.add_child(folium.Circle(
                                location=[row['lat'], row['lon']],
                                radius=150,
                                color="#3186cc",
                                fill=True,
                                fill_color="#3186cc")
                                )
        feature_group_y.add_child(folium.Circle(
                                location=[row['lat'], row['lon']],
                                radius=150,
                                color="#ede737",
                                fill=True,
                                fill_color="#ede737")
                                )

    m.add_child(feature_group_b)
    m.add_child(feature_group_y)

    mc_b = MarkerCluster(name="Cluster blue", show=False)
    mc_y = MarkerCluster(name="Cluster yellow", show=False)
    # Add the points as markers
    for idx, row in latlon_pointsGDF.iterrows():
        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=150,
            color="#3186cc",
            fill=True,
            fill_color="#3186cc",
        ).add_to(mc_b)
        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=150,
            color="#ede737",
            fill=True,
            fill_color="#ede737",
        ).add_to(mc_y)
        
    mc_b.add_to(m)
    mc_y.add_to(m)

    # Show controls
    folium.LayerControl().add_to(m)
    # Save map
    m.save(f"{path}/{name}.html")


def create_train_val_test(points, degrees, method, ratios, seed):
    # Set the seed for random number generation
    random.seed(seed)

    if method == 'checkerboard':
        train_points, val_points, test_points = [], [], []
        for lat, lon in points:
            # Calculate the grid coordinates based on degrees
            lat_coord = int(lat / degrees)
            lon_coord = int(lon / degrees)

            # Assign points to train, val, or test based on grid position
            if lat_coord % 2 == 0 or lon_coord % 2 == 0:
                train_points.append((lat, lon))
            elif lat_coord % 2 == 1 and lon_coord % 4 == 1:
                val_points.append((lat, lon))
            else:
                test_points.append((lat, lon))
            # else:
            #     if random.random() < 0.5:
            #         val_points.append((lat, lon))
            #     else:
            #         test_points.append((lat, lon))

        return train_points, val_points, test_points

    elif method == 'random':        
        # Shuffle the points randomly
        random.shuffle(points)

        # Determine the number of points for each split
        total_points = len(points)
        train_size = int(ratios[0] * total_points)
        val_size = int(ratios[1] * total_points)

        # Split the points into train, val, and test sets
        train_points = points[:train_size]
        val_points = points[train_size:train_size + val_size]
        test_points = points[train_size + val_size:]

        return train_points, val_points, test_points

    else:
        raise ValueError("Invalid method provided. Supported methods: 'checkerboard', 'random'")

def points_to_gdf(points, epsg):
    lon = [point[0] for point in points]
    lat = [point[1] for point in points]
    point_geometry = gpd.points_from_xy(lon, lat)
    gdf_points = gpd.GeoDataFrame(geometry=point_geometry, crs=epsg)
    gdf_points['lon'] = lon
    gdf_points['lat'] = lat
    return gdf_points


def folium_group_points(points, name, radius, color, fill=True):
    feature_group = folium.FeatureGroup(f'{name}-{color}')
    for idx, row in points.iterrows():
        feature_group.add_child(folium.Circle(
                                location=[row['lat'], row['lon']],
                                radius=radius,
                                color=color,
                                fill=fill,
                                fill_color=color)
                                )
    return feature_group


def save_folium_map_train_val_test(train_gdf, val_gdf, test_gdf, path, name):
    
    # Create a folium map centered around the mean coordinates of the points
    center_lat = train_gdf['lat'].mean()
    center_lon = train_gdf['lon'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
    for layer in ['stamentoner','stamenterrain', 'cartodbpositron', 'cartodbdark_matter', 'stamenwatercolor']:
        folium.TileLayer(layer).add_to(m)


    train_group = folium_group_points(train_gdf, "Train", 150, "blue")
    val_group = folium_group_points(val_gdf, "Validation", 150, "red")
    test_group = folium_group_points(test_gdf, "Test", 150, "green")

    m.add_child(train_group)
    m.add_child(val_group)
    m.add_child(test_group)

    # Show controls
    folium.LayerControl().add_to(m)
    # Save map
    m.save(f"{path}/{name}.html")