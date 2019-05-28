#!/usr/bin/env python3


import argparse
import collections
import functools
import itertools
import json
import multiprocessing
import numpy as np
import os
from pathlib import Path
import PIL
import pyedflib
import scipy
from scipy import signal


# argpare arguments
parser = argparse.ArgumentParser()
parser.add_argument('--dict_string', default='data_dict.json', type=str,
        help='The string for the dictionary to use')

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
    img_path = data_path/'images'
    return parent_path, test_path, img_path


def eeg_to_image(data, fn, image_path):
    S = np.fft.fft(data)
    D = divergence(S)
    S, D = abs(S), abs(D)
    I = convolve_8NNavg(D)
    S, D, I = scale(S), scale(D), scale(I)
    img = np.stack([S, D, I], axis=2)
    save_loc = f'{image_path/fn}.png'
    save_image(save_loc, img)


def build_filename(key, entry, h, w ,op, st, et, p, tp):
    date = entry['date'].replace('/','_')
    s = entry['session']
    c = entry['config']
    t = entry['segment']
    ts = entry['total_segments']
    ch = entry['channels']
    if entry['type'] == 'dev_test':
        return f"test/{c}_{key}_s{s}_d{date}_t{t}_ts{ts}_ch{ch.zfill(3)}_h{h}_w{w}_o{o}_st{str(st).zfill(8)}_et{str(et).zfill(8)}_p{str(p).zfill(5)}_tp{str(tp).zfill(5)}"
    return f"train/{c}_{key}_s{s}_d{date}_t{t}_ts{ts}_ch{ch.zfill(3)}_h{h}_w{w}_o{o}_st{str(st).zfill(8)}_et{str(et).zfill(8)}_p{str(p).zfill(5)}_tp{str(tp).zfill(5)}"


def save_image(save_loc, img):
    img = PIL.Image.fromarray(img, 'RGB')
    img = img.resize([224,224], PIL.Image.ANTIALIAS)
    img.save(save_loc)


def get_data_dictionary(parent_path, dict_string):
    with open(parent_path/dict_string,'r') as f:
        data_dict = json.load(f)
    return data_dict


def down_sample_eeg(entry, h):
    f = pyedflib.EdfReader(entry['loc'])
    n = f.signals_in_file
    signal_labels = f.getSignalLabels()
    eeg = np.zeros((n, f.getNSamples()[0]))
    for i in np.arange(n):
        eeg[i, :] = f.readSignal(i)
    num_elems = int(float(entry['durations'][-1])) * h
    return signal.resample(eeg, num=num_elems, axis=1)


def process_eeg(eeg, key, entry, h, w, o, label_dict, image_path):
    length = float(entry['durations'][-1])
    step_value = w - (w * (o/100))
    piece = 1 
    total_pieces = len(np.arange(0, length, step_value))
    for start in np.arange(0, length, step_value):
        end = start + w
        fn = build_filename(key, entry, h, w, o, start, end, piece,
                total_pieces)
        start_obs = int(start * h)
        end_obs = int(end * h)
        new_eeg = eeg[::,start_obs:end_obs]
        eeg_to_image(new_eeg, fn, image_path)
        write_labels(start, end, entry, fn, label_dict)
        piece += 1

def get_labels(start, end, label_durations):
    labels = set()
    for (label_start, label_end), label in label_durations:
        if start >= label_start and start < label_end:
            labels.add(label)
        if end >= label_start and end < label_end:
            labels.add(label)
    if len(labels) > 1:
        labels.remove('bckg')
    return labels


def get_durations(entry):
    durations = []
    for i, dur in enumerate(entry['durations']):
        if i == 0:
            durations.append((0, float(dur)))
        else:
            durations.append((float(entry['durations'][i-1]), float(dur)))
    return zip(durations, entry['labels'])


def write_labels(start, end, entry, fn, label_dict):
    label_durations = get_durations(entry)
    labels = get_labels(start, end, label_durations)
    label_dict[f'{fn}.png'] = labels


def get_eeg(entry): 
    f = pyedflib.EdfReader(entry['loc'])
    n = f.signals_in_file
    signal_labels = f.getSignalLabels()
    sigbufs = np.zeros((n, f.getNSamples()[0]))
    for i in np.arange(n):
        sigbufs[i, :] = f.readSignal(i)
    return sigbufs

if __name__ == "__main__":
    args = parser.parse_args()
    parent_path, test_path, img_path = get_paths()
    data_dict = get_data_dictionary(parent_path, args.dict_string)

    num_eegs = (len([item for sublist in data_dict.values() for item in sublist]))
    print(f'Number of EEGs: {num_eegs}')
    
    ## process eegs (multiprocessing)
    
    H_VALUES = (12,24,48,64,96)
    W_VALUES = (1,2,4,6,8)
    O_VALUES = (25,50,75)
    
    label_dict = collections.defaultdict()
    for key, entries in data_dict.items():
        for observation in entries:
            try:
                eeg = get_eeg(observation)
            except:
                print(observation)
                continue
            for h in H_VALUES:
                down_sampled_eeg = down_sample_eeg(observation, h)
                for w, o in list(itertools.product(W_VALUES, O_VALUES)):
                    process_eeg(down_sampled_eeg, key, observation, h, w, o,
                            label_dict, img_path) 
    
    ## turn into images (how to pass them to this)
    # for f in test_path.iterdir():
    #     p = multiprocessing.Process(target=eeg_to_image, args=(f, test_path, img_path))
    #     p.start() 

