import collections
import functools
from pathlib import Path
import PIL
import os
import numpy as np
import scipy
from scipy import signal
import multiprocessing

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
    data_path = here.parent/'data'
    test_path = data_path/'augmented/test'
    img_path = data_path/'images/test'
    return test_path, img_path

def eeg_to_image(f, test_path, img_path):
    data = np.load(f)
    save_loc = img_path/f'{f.stem}.png'
    S = np.fft.fft(data)
    D = divergence(S)
    S = abs(S)
    D = abs(D)
    I = convolve_8NNavg(D)
    S = scale(S)
    D = scale(D)
    I = scale(I)
    img = np.stack([S,D,I], axis=2)
    img = PIL.Image.fromarray(img, 'RGB')
    img = img.resize([224,224], PIL.Image.ANTIALIAS)
    img.save(save_loc)

if __name__ == "__main__":
    test_path, img_path = get_paths()
    for f in test_path.iterdir():
        p = multiprocessing.Process(target=eeg_to_image, args=(f, test_path, img_path))
        p.start()

