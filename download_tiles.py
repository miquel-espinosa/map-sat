import numpy as np
import os
import subprocess
import math
from concurrent.futures import ThreadPoolExecutor
import glob
import time

import argparse

def parse_args():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Command line arguments.')

    # Add arguments
    parser.add_argument('--pfile',
                        type=str,
                        required=True,
                        help='Points file, the id of the file. Example: central-belt50.')
    
    parser.add_argument('--zoom',
                        type=int,
                        default=17,
                        help='Zoom level.')
    parser.add_argument('--threads',
                        type=int,
                        default=os.cpu_count(),
                        help='Number of threads to use.')
    parser.add_argument('--apis',
                        type=str,
                        nargs='+',
                        default=['worldimagery-clarity', 'openstreetmap'],
                        help='APIs to use. Example: worldimagery-clarity, openstreetmap.')
    parser.add_argument('--root',
                        type=str,
                        default=os.getcwd(),
                        help='Root folder.')
    parser.add_argument('--save_root',
                        type=str,
                        default='dataset',
                        help='Root folder to save the tiles.')

    # Parse the arguments
    args = parser.parse_args()
    
    # HACK: Manually set the arguments
    args.coords_path = f'{args.root}/results/{args.pfile}'
    args.tiles_path = f'{args.save_root}/tiles_{args.pfile}'

    return args

# API urls
APIS = {
    'worldimagery' : 'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    'worldimagery-clarity': 'https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    'openstreetmap' : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    'ukosgb1888': 'https://api.maptiler.com/tiles/uk-osgb10k1888/{z}/{x}/{y}.jpg?key=MXVhdLdJmHeZ0z5DwjBI'
}

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def format_string(url, x, y, zoom):
    substituted_string = url.replace('{x}', str(x))
    substituted_string = substituted_string.replace('{y}', str(y))
    substituted_string = substituted_string.replace('{z}', str(zoom))
    return substituted_string

def download_tile(url, tile_path, max_retries=5, retry_delay=2):
    retries = 0
    while retries < max_retries:
        try:
            subprocess.run(["curl", url, '--output', tile_path], check=True)
            return  # Download successful, exit the function
        except subprocess.CalledProcessError as e:
            print(f"Download failed: {e}")
            retries += 1
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached, giving up.")

def main():
    
    args = parse_args()
    
    if not os.path.exists(args.tiles_path):
        os.makedirs(args.tiles_path)
    
    # Create folders for the different image types
    for url in args.apis:
        if not os.path.exists(f'{args.tiles_path}/{url}'):
            os.makedirs(f'{args.tiles_path}/{url}')
    
    # existing_files = {}
    # for url in APIS:
    #     existing_files[url] = glob.glob(f'{TILES_PATH}/{url}/*.png')
    
    # Load the coordinates
    coordinates = np.load(f'{args.coords_path}/{args.pfile}.npy')

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        
        for coord in coordinates:
            lon, lat = coord[0], coord[1]
            x, y = deg2num(lat, lon, zoom=args.zoom)
            
            for url in args.apis:
                tile_url = format_string(APIS[url], x, y, args.zoom)
                tile_path = f'{args.tiles_path}/{url}/{args.zoom}_{x}_{y}.png'
                future = executor.submit(download_tile, tile_url, tile_path)
                futures.append(future)
        
        # Wait for all the downloads to complete
        for future in futures:
            future.result()

if __name__ == '__main__':
    main()
