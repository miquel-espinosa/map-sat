import geopandas as gpd
from shapefile_utils import lat_lon_to_epsg, create_rectangle_shapefile, \
                            intersect_shapefiles, create_polygon, change_lat_with_lon, \
                            save_folium_map, generate_random_points_within_shapefile_parallel
import matplotlib.pyplot as plt
import os
import numpy as np
import argparse

def parse_args():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Command line arguments.')

    parser.add_argument('--npoints',
                        type=int,
                        required=True,
                        help='Number of points to generate.')
    
    parser.add_argument('--name',
                        type=str,
                        default='sct',
                        required=True,
                        help='Name of the region. Example: edi, sct, central-belt.')
    
    parser.add_argument('--root',
                        type=str,
                        default=os.getcwd(),
                        help='Root folder.')
    parser.add_argument('--seed',
                        type=int,
                        default=42,
                        help='Seed for the random generator.')
    parser.add_argument('--plots',
                        action='store_true',
                        default=True,
                        help='Create plots.')
    parser.add_argument('--show',
                        action='store_true',
                        default=False,
                        help='Show plots.')
    parser.add_argument('--folium',
                        action='store_true',
                        default=True,
                        help='Create folium map.')
    parser.add_argument('--epsg',
                        type=str,
                        default='EPSG:4326',
                        help='EPSG code.')

    # Parse the arguments
    args = parser.parse_args()
    
    # HACK: Manually set the arguments
    args.shp_sct_path = f'{args.root}/country_data/scotland.shp'
    args.path_figs = f'{args.root}/results'
    args.coord_path = f'{args.path_figs}/{args.name}{args.npoints}'
    
    return args



def main():
    
    args = parse_args()
    
    # Create directories for figures and results if they dont exist
    if not os.path.exists(args.coord_path):
        os.makedirs(args.coord_path)
        
    # ----------------- Scotland shapefile ---------------
    # Read the shapefile for Scotland
    sct_inland = gpd.read_file(args.shp_sct_path)
    
    if args.name == 'edi':
        # ----------------- Square (edinburgh) shapefile ---------------
        lat_lon_min = (-3.30, 55.88) # lat, lon
        lat_lon_max = (-3.08, 55.99) # lat, lo
        # Create a rectangle shapefile for Edinburgh area
        edinburgh_shapefile = create_rectangle_shapefile(lat_lon_min, lat_lon_max, crs=args.epsg)

        # ----------------- Intersection shapefile ---------------
        # Intersect the two shapefiles into a common CRS
        final_shapefile = intersect_shapefiles(edinburgh_shapefile, sct_inland, crs="EPSG:4326")
    elif args.name == 'central-belt':
        # ----------------- Polygon (central belt) shapefile ---------------
        # lat_lon_min = lat_lon_to_epsg(55.88, -3.30, epsg=scotland_shapefile.crs)
        # lat_lon_max = lat_lon_to_epsg(55.99, -3.08, epsg=scotland_shapefile.crs)
        coordinates = ((55.950010, -2.381500), (56.499314, -2.808075), (56.434390, -3.543699),
                    (56.151770, -4.070388), (55.918314, -5.010594), (55.405161, -4.679781))
        coordinates = change_lat_with_lon(coordinates)
        # Create a polygon shapefile for Central Belt area
        central_belt_shapefile = create_polygon(coordinates, crs=args.epsg)
        
        # ----------------- Intersection shapefile ---------------
        # Intersect the two shapefiles into a common CRS
        final_shapefile = intersect_shapefiles(central_belt_shapefile, sct_inland, crs="EPSG:4326")
    else:
        final_shapefile = sct_inland

    print("Generating points...")
    # Generate random points within the shapefile, latitude range, and longitude range
    random_points = generate_random_points_within_shapefile_parallel(final_shapefile, num_points=args.npoints, seed=args.seed)
    print("Points generated")
    np.save(f'{args.coord_path}/{args.name}{args.npoints}.npy', random_points)

    # Print the generated points
    # for point in random_points:
    #     print(f"Latitude: {point[0]}, Longitude: {point[1]}")

    lon = [point[0] for point in random_points]
    lat = [point[1] for point in random_points]
    point_geometry = gpd.points_from_xy(lon, lat)
    gdf_points = gpd.GeoDataFrame(geometry=point_geometry, crs=final_shapefile.crs)
    gdf_points['lon'] = lon
    gdf_points['lat'] = lat
    
    if args.plots:
        # Plot the random points
        fig, ax = plt.subplots()
        ax.axis('off')
        final_shapefile.plot(ax=ax, color='lightgrey', edgecolor='black')
        gdf_points.plot(ax=ax, color='darkblue', markersize=5)
        plt.savefig(f'{args.coord_path}/{args.name}{args.npoints}.png', dpi=300, bbox_inches='tight')
        if args.show:
            plt.show()
            
    if args.folium:
        save_folium_map(gdf_points, args.coord_path, f'{args.name}{args.npoints}')
        
if __name__=='__main__':
    main()