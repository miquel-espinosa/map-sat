# Generate Your Own Scotland

**UPDATE: 🎉 Our paper has been accepted at [NeurIPS 2023 Workshop on Diffusion Models](https://diffusionworkshop.github.io/)!!!**

- [Arxiv Paper](https://arxiv.org/abs/2308.16648)
- [NeurIPS Workshop Paper (extension)](http://nbviewer.jupyter.org/github/miquel-espinosa/map-sat/blob/main/imgs/NeurIPS_Workshop_23_Diffusion_Models.pdf)

## _Satellite Image Image Generation Conditioned on Maps_ 🗺️ -> 🛰️ 🏞️

> _We show that state-of-the-art pretrained diffusion models can be conditioned on cartographic data to generate realistic satellite images. We train the ControlNet model and qualitatively evaluate the results, demonstrating that both image quality and map fidelity are possible._

Below are the results of our model. The first column shows the input map, the second column shows the real satellite image, and the rest show the generated satellite images with diffusion models (ControlNet) when conditioned on the OSM map.

![examples image](imgs/examples.png)

We also present the results obtained when generating satellite images that follow the layout of historical maps from 1888. The first column shows the input historical map (1888), the second column shows the real satellite image (2017), and the rest show the generated satellite images with diffusion models (ControlNet) when conditioned on the historical map.

![examples image](imgs/neurips-historical-maps.png)

## Installation
Create a conda environment and install the dependencies
```
conda create -n mapsat python=3.7
conda activate mapsat
pip install -r requirements.txt
```

## Steps
### Download and preprocess shapefiles
First, download the shapefile data for scotland. This will generate a folder called `country_data` with the shapefile data for the country of Great Britain.
```
./download_data.sh
```
Next, we will split the shapefile into the region of Scotland (merge into single file), and further select only mainland sctoland.
```
python create_shapefile_scotland.py
```

### Sample points
To sample points, we will use the script `generate_points.py`. This file will accept multiple command line arguments. It is required to specify the following:
- `--npoints`: the number of points to sample
- `--name`: the name of the region to sample points from. Currently the script only accepts: `edi` (edinburgh) or `sct` (scotland) or `central-belt` (central-belt)

![shapefile image](imgs/regions.png)

For instance, to sample 1000 points from the central belt of Scotland, run the following:
```
python generate_points.py --npoints 1000 --name central-belt
```
This will generate a subfolder in `results/` called `central-belt1000` with the following files:
- `central-belt1000.html`: a folium dynamic visualisation of the sampled points in an interactive map.
- `central-belt1000.png`: a png image of the region with the sampled points
- `central-belt1000.npy`: a npy file containing the sampled points in the form of a numpy array of shape (npoints, 2), where the first column is the longitude and the second column is the latitude.

### Download tiles
Lastly, we will download the tiles using the script `download_tiles.py`. This script will accept the following command line arguments:
- `--pfile`: this is the identifier of the points file to use. For instance, if we want to use the points file `central-belt1000.npy`, then we would specify `--pfile central-belt1000`

For instance, to download the tiles for the points file `central-belt1000.npy`, run the following (assuming the points file has already been generated):
```
python download_tiles.py --pfile central-belt1000
```

The image below shows some paired samples from the different datasets as downloaded with the above script.

<p align="center">
  <img src="imgs/datasets.png" width=50% height=50%>
</p>

## Model training
We train a ControlNet model with the built dataset using the code provided by the [diffusers library](https://github.com/huggingface/diffusers/tree/main/examples/controlnet). It is recommended to compile the dataset as a [huggingface dataset](https://huggingface.co/docs/datasets/index).

## Model weights

The best performing model, trained on the Central Belt dataset, is publicly available at https://huggingface.co/mespinosami/controlearth.

We also publish the model trained on Mainland Scotland at https://huggingface.co/mespinosami/controlearth-sct for comparative purposes.

## Using the model
(Note that the model was trained on OSM tiles at zoom level 17, so make sure that the zoom level you are using is the same.)

1. Download an OSM image of your liking. E.g: two images from Edinburgh city (OSM map at zoom=17)
```
wget https://datasets-server.huggingface.co/assets/mespinosami/map2sat-edi5k20-samples/--/default/train/11/input_image/image.png -O image1.png
wget https://datasets-server.huggingface.co/assets/mespinosami/map2sat-edi5k20-samples/--/default/train/1/input_image/image.png -O image2.png
```
2. Generate multiple images for each OSM tile:
```python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
from PIL import Image
import torch
controlnet = ControlNetModel.from_pretrained("mespinosami/controlearth", torch_dtype=torch.float16)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5", controlnet=controlnet, torch_dtype=torch.float16,
        safety_checker = None, requires_safety_checker = False
    )
    
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()

control_image_1 = Image.open('./image1.png').convert("RGB")
control_image_2 = Image.open('./image2.png').convert("RGB")
prompt = "convert this openstreetmap into its satellite view"

num_images = 5
for i in range(num_images):
    image = pipe(prompt, num_inference_steps=50, image=control_image_1).images[0].save(f'img1-generated-{i}.png')
for i in range(num_images):
    image = pipe(prompt, num_inference_steps=50, image=control_image_2).images[0].save(f'img2-generated-{i}.png')
```
3. Images generated will look similar to these:
![example-github-1](https://github.com/miquel-espinosa/map-sat/assets/34089118/455a1e29-f92f-49dc-93c2-b27a9fe524aa)

## Citation
If you find this work helpful please consider citing
```
@article{espinosa_2023_8_mapsat,
  	author = {Miguel Espinosa and Elliot J. Crowley},
  	title = {Generate Your Own Scotland: Satellite Image Generation Conditioned on Maps},
  	year = {2023},
  	month = {Aug},
  	journal = {NeurIPS 2023 Workshop on Diffusion Models},
  	institution = {University of Edinburgh},
  	url = {https://arxiv.org/abs/2308.16648},
}
