#!/usr/bin/env python3


import argparse
import collections
import functools
import json
import multiprocessing
import numpy as np
import os
from pathlib import Path
import PIL
import scipy
from scipy import signal


# argpare arguments


def divergence(F):
    """ compute the divergence of n-D scalar field `F` """
    """ https://stackoverflow.com/questions/11435809/compute-divergence-of-vector-field-using-python """
    return functools.reduce(np.add,np.gradient(F))


def scale(F):
    """ scale a n-D scalar field to [0-255] range for image creation """
    F *= (255.0/F.max())
    return F


def convolve_8NNavg(F):
    """ compute the average of the 8 nearest neighbors for each point in the n-D scalar field `F` """
    """ https://gis.stackexchange.com/questions/254753/calculate-the-average-of-neighbor-pixels-for-raster-edge """
    return scipy.ndimage.generic_filter(F, np.nanmean, size=3, mode='constant', cval=np.NaN)


def get_paths():
    here = Path(f'{os.getcwd()}')
    parent_path = here.parent
    data_path = parent_path/'data'
    test_path = data_path/'augmented/test'
    img_path = data_path/'images/test'
    return parent_path, test_path, img_path


def eeg_to_image(f, test_path, img_path):
    data = np.load(f)
    save_loc = img_path/f'{f.stem}.png'
    S = np.fft.fft(data)
    D = divergence(S)
    S, D = abs(S), abs(D)
    I = convolve_8NNavg(D)
    S, D, I = scale(S), scale(D), scale(I)
    img = np.stack([S, D, I], axis=2)
    save_image(save_loc, img)


def save_image(save_loc, img):
    img = PIL.Image.fromarray(img, 'RGB')
    img = img.resize([224,224], PIL.Image.ANTIALIAS)
    img.save(save_loc)


def get_data_dictionary(parent_path):
    with open(parent_path/'data_dict.json','r') as f:
        data_dict = json.load(f)
    return data_dict


if __name__ == "__main__":
    parent_path, test_path, img_path = get_paths()
    data_dict = get_data_dictionary(parent_path)
    ## process eegs (multiprocessing)
    ## turn into images (how to pass them to this)
    # for f in test_path.iterdir():
    #     p = multiprocessing.Process(target=eeg_to_image, args=(f, test_path, img_path))
    #     p.start() 

