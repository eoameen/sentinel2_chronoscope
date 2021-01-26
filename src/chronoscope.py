from typing import List, Tuple
import argparse

import os
import glob
import tempfile

import xml.etree.ElementTree as et
import numpy as np
from shapely import geometry
import rasterio
from rasterio import warp
from rasterio.windows import from_bounds
import cv2
import imageio

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# list of bands and their order in final animation
bands = [
#     "R20m/B12.jp2",
    "R20m/B8A.jp2",
    "R20m/B07.jp2",
    "R20m/B06.jp2",
#     "R20m/B11.jp2",
    "R20m/B05.jp2",
    "R10m/B04.jp2",
    "R10m/B03.jp2",
    "R20m/B08.jp2",
    "R10m/B02.jp2",
    "R10m/B02.jp2",
    "R10m/B02.jp2",
    "R10m/B02.jp2"
]


def get_scene_footprint(band_path: str) -> geometry.polygon.Polygon:
    """return S2 scene footprint in lon/lat"""
    with rasterio.open(band_path) as dataset:
        footprint = dataset.bounds
        mins = warp.transform(
            dataset.crs,
            {"init": "epsg:4326"},
            [dataset.bounds[0]], [dataset.bounds[1]]
            )
        maxs = warp.transform(
            dataset.crs,
            {"init": "epsg:4326"},
            [dataset.bounds[2]], [dataset.bounds[3]]
            )
    # return footprint as polygon
    footprint = geometry.Polygon([
        [mins[0][0], maxs[1][0]],
        [maxs[0][0], maxs[1][0]],
        [maxs[0][0], mins[1][0]],
        [mins[0][0], mins[1][0]]]
    )
    return footprint


def check_window(
    footprint: geometry.polygon.Polygon,
    bounds: Tuple
    ) -> bool:
    """check if input window is inside scene"""
    window = geometry.Polygon(
        [[bounds[2], bounds[1]],
         [bounds[2], bounds[3]],
         [bounds[0], bounds[3]],
         [bounds[0], bounds[1]]
        ])
    return footprint.contains(window)


def load_crop(
    band_path: str,
    bounds: Tuple,
    resample_flag: bool,
    scale_factor: float
    ) -> np.ndarray:
    """return a raster crop given band path and window"""
    # convert bounds from lat/lon to meters
    with rasterio.open(band_path) as src:
        crs_data = src.crs.data
    mins = warp.transform(
        {"init": "epsg:4326"},
        crs_data,
        [bounds[0]],
        [bounds[1]]
    )
    maxs = warp.transform(
        {"init": "epsg:4326"},
        crs_data,
        [bounds[2]],
        [bounds[3]]
    )
    # load crop
    with rasterio.open(band_path) as dataset:
        width = dataset.width
        height = dataset.height
        crop = dataset.read(
            1,
            window=from_bounds(
                mins[0][0],
                mins[1][0],
                maxs[0][0],
                maxs[1][0],
                dataset.transform)
        )
    # upsample bands with GSD > 10m
    if resample_flag:
        crop = cv2.resize(
            crop,
            dsize=(
                int(scale_factor * np.shape(crop)[1]),
                int(scale_factor * np.shape(crop)[0])
            ),
            interpolation=cv2.INTER_CUBIC
        )
    return crop


def scale_down(img: np.ndarray) -> np.ndarray:
    """scale down pixel values to 8 bit"""
    (mean, std) = cv2.meanStdDev(img)
    maxval = (mean[0][0] + 2.0 * std[0][0])
    img = cv2.convertScaleAbs(img, alpha=(255 / maxval)).astype(np.uint8)
    return(img)


def make_gif(frames: List[np.ndarray], output_path: str, fps: int) -> str:
    """make a gif given a list of S2 scene bands"""
    # write frames to disk temporarily
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i in range(len(frames)):
            frame = scale_down(frames[i])
            cv2.imwrite(os.path.join(tmp_dir, "{:02d}.png").format(i), frame)
            images = []
            for filename in sorted(glob.glob(os.path.join(tmp_dir, '*.png'))):
                images.append(imageio.imread(filename))
            imageio.mimsave(output_path, images, duration=float(1 / fps))
    return output_path


def prep_frames(bands: List, scene: str, bounds: Tuple) -> np.ndarray:
    """prepare gif frames"""
    frames = []
    for band, i in zip(bands, range(len(bands))):
        if band.split("/")[0] == "R10m":
            crop = load_crop(os.path.join(scene, band), bounds, False, 2.0)
        elif band.split("/")[0] == "R20m":
            crop = load_crop(os.path.join(scene, band), bounds, True, 2.0)
        else:
            crop = load_crop(os.path.join(scene, band), bounds, True, 3.0)
        # make sure all frames have same dimensions after resampling
        if i == 0:
            h, w = np.shape(crop)
        crop = cv2.resize(crop, dsize=(w, h), interpolation=cv2.INTER_CUBIC)
        frames.append(crop)
    return frames


def chronoscope(scene: str, fps: int, window: List[float], output: str) -> str:
    """generate animated gif given S2 scene"""
    # get scene footprint in lat/lon
    footprint = get_scene_footprint(os.path.join(scene, "R10m/B02.jp2"))
    # check if input window falls inside scene
    if not check_window(footprint, tuple(window)):
        raise ValueError("window falls outside scene bounds")
    # make gif
    os.makedirs(output, exist_ok=True)
    frames = prep_frames(bands, scene, tuple(window))
    gif_path = make_gif(frames, os.path.join(output, "scene.gif"), fps)
    logging.info(f"animated gif wriiten to: {gif_path}")
    return gif_path



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--scene",
        help="path to S2 scene directory",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-f",
        "--frame_rate",
        help="frames per second (fps)",
        type=int,
        default=5,
    )
    parser.add_argument(
        "-w",
        "--window",
        type=float,
        nargs="*",
        help="bounds (Xmin Ymin Xmax Ymax) in lat/lon",
        required=True
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output directory. Default is output/.",
        type=str,
        default="output",
    )
    args = parser.parse_args()
    chronoscope(args.scene, args.frame_rate, args.window, args.output)
