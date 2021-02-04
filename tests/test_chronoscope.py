import os

import pytest

from shapely import geometry
import numpy as np

from conftest import INVALID_WINDOW, VALID_WINDOW, SCENE_PATH, BAND_PATH

from src.chronoscope import (
    bands,
    get_scene_footprint,
    check_window,
    load_crop,
    scale_down,
    make_gif,
    prep_frames,
    chronoscope
    )


# tests for get_scene_footprint()
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH},
    ],
)
def test_get_scene_footprint(test_input):
    footprint = get_scene_footprint(band_path=test_input['band_path'])
    assert isinstance(footprint, geometry.polygon.Polygon)


# tests for check_window()
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH, "window": VALID_WINDOW},
    ],
)
def test_check_window(test_input):
    footprint = get_scene_footprint(band_path=test_input['band_path'])
    assert check_window(footprint, tuple(test_input['window']))


# tests for load_crop()
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH, "window": VALID_WINDOW, "resample_flag": True, "scale_factor": 2.0},
        # case 2
        {"band_path": BAND_PATH, "window": VALID_WINDOW, "resample_flag": True, "scale_factor": 3.0},
        # case 3
        {"band_path": BAND_PATH, "window": VALID_WINDOW, "resample_flag": False, "scale_factor": 2.0},

    ],
)
def test_load_crop(test_input):
    crop = load_crop(test_input['band_path'], tuple(test_input['window']), test_input['resample_flag'], test_input['scale_factor'])
    assert isinstance(crop, np.ndarray)


# tests for scale_down()
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH, "window": VALID_WINDOW, "resample_flag": True, "scale_factor": 2.0},
        # case 2
        {"band_path": BAND_PATH, "window": VALID_WINDOW, "resample_flag": False, "scale_factor": 2.0},

    ],
)
def test_scale_down(test_input):
    crop = load_crop(test_input['band_path'], tuple(test_input['window']), test_input['resample_flag'], test_input['scale_factor'])
    scaled_crop = scale_down(crop)
    assert isinstance(scaled_crop, np.ndarray)


# tests for prep_frames()
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH, "bands": bands, "scene_path": SCENE_PATH, "window": VALID_WINDOW},
    ],
)
def test_prep_frames(test_input):
    footprint = get_scene_footprint(band_path=test_input['band_path'])
    frames = prep_frames(test_input['bands'], test_input['scene_path'], tuple(test_input['window']))
    assert isinstance(frames, list)


# tests for make_gif()
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH, "bands": bands, "scene_path": SCENE_PATH, "window": VALID_WINDOW, "frame_rate": 3},
    ],
)
def test_make_gif(test_input, tmpdir):
    footprint = get_scene_footprint(band_path=test_input['band_path'])
    frames = prep_frames(test_input['bands'], test_input['scene_path'], tuple(test_input['window']))
    gif_path = make_gif(frames, os.path.join(tmpdir, "scene.gif"), test_input["frame_rate"])
    assert os.path.exists(gif_path)

# tests for chronoscope() using valid input
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH, "scene_path": SCENE_PATH, "window": VALID_WINDOW, "frame_rate": 3},
    ],
)
def test_chronoscope_valid(test_input, tmpdir):
    gif_path = chronoscope(test_input['scene_path'], test_input['frame_rate'], test_input['window'], tmpdir)
    assert os.path.exists(gif_path)


# tests for chronoscope() using invalid input
@pytest.mark.parametrize(
    "test_input",
    [
        # case 1
        {"band_path": BAND_PATH, "scene_path": SCENE_PATH, "window": INVALID_WINDOW, "frame_rate": 3},
    ],
)
def test_chronoscope_invalid(test_input, tmpdir):
    with pytest.raises(ValueError):
        chronoscope(test_input['scene_path'], test_input['frame_rate'], test_input['window'], tmpdir)
