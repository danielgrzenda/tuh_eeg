#/usr/bin/env python3


import argparse
import collections
import csv
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
from scipy import stats
from scipy import signal
import time

# argpare arguments
parser = argparse.ArgumentParser()
parser.add_argument('--dict_string', default='data_dict.json', type=str,
        help='The string for the dictionary to use')

CHANNEL_NAMES = ['EEG FP1-REF','EEG FP2-REF','EEG F8-REF',
                 'EEG F4-REF','EEG FZ-REF','EEG F3-REF',
                 'EEG F7-REF','EEG A1-REF','EEG T3-REF',
                 'EEG C3-REF','EEG CZ-REF','EEG C4-REF',
                 'EEG T4-REF','EEG A2-REF','EEG T6-REF',
                 'EEG P4-REF','EEG PZ-REF','EEG P3-REF',
                 'EEG T5-REF','EEG O1-REF','EEG O2-REF']

def divergence(X):
    """ compute the divergence of n-D scalar field `X` """
    return scipy.ndimage.laplace(X)


def scale(X, maxi=255, mini=0):
    """ scale a n-D scalar field to [0-255] range for image creation """
    X_std = (X - X.min()) / (X.max() - X.min())
    X_scaled = X_std * (maxi - mini) + mini
    return X_scaled


def convolve_8NNavg(F):
    """ compute the average of the 8 nearest neighbors for each point in the n-D scalar field `F` """
    """ https://gis.stackexchange.com/questions/254753/calculate-the-average-of-neighbor-pixels-for-raster-edge """
    return scipy.ndimage.generic_filter(F, np.nanmean, size=3, mode='constant', cval=np.NaN)


def l2_row(X):
    norm = np.linalg.norm(X, axis=1)[:,np.newaxis]
    if not np.all(norm):
        print(norm)
    X /=  np.linalg.norm(X, axis=1)[:,np.newaxis]
    return X  


def get_paths():
    here = Path(f'{os.getcwd()}')
    parent_path = here.parent
    data_path = parent_path/'data'
    raw_path = data_path/'raw'/'v1.5.0/edf'
    train_path = raw_path/'train'
    test_path = raw_path/'test'
    img_path = data_path/'images'
    paths = {'parent':parent_path, 'raw':raw_path, 'train':train_path, 
            'test':test_path, 'image':img_path}
    return paths


def eeg_to_image(data, fn, image_path):
    S = np.abs(np.fft.fft(data, axis=1))
    D = divergence(S)
    I = convolve_8NNavg(D)
    S, D, I = l2_row(S), l2_row(D), l2_row(I) 
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
    img = PIL.Image.fromarray(img.astype(np.uint8), 'RGB').resize((224,224))
    img.save(save_loc)


def get_data_dictionary(parent_path, dict_string):
    with open(parent_path/dict_string,'r') as f:
        data_dict = json.load(f)
    return data_dict


def down_sample_eeg(eeg, entry, h):
    num_elems = int(float(entry['durations'][-1])) * h
    data = np.empty((eeg.shape[0], num_elems), np.float64)
    for idx, channel in enumerate(eeg):
        data[idx] = scipy.signal.resample(channel, num=num_elems)
    return data


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


def get_labels(start, end, label_durations, entry):
    labels = set()
    for (label_start, label_end), label in label_durations:
        if start >= label_start and start < label_end:
            labels.add(label)
        if end >= label_start and end < label_end:
            labels.add(label)
    if len(labels) > 1:
        try:
            labels.remove('bckg')
        except:
            print(start, end, entry)
            pass
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
    labels = get_labels(start, end, label_durations, entry)
    label_dict[f'{fn}.png'] = labels


def get_eeg(entry): 
    with pyedflib.EdfReader(entry['loc']) as f:
        n = f.signals_in_file
        signal_labels = f.getSignalLabels()
        sigbufs = np.zeros((len(CHANNEL_NAMES), f.getNSamples()[0]))
        channel_list = [i for i,ch in enumerate(signal_labels) if ch in CHANNEL_NAMES]
        max_len = max(f.getNSamples())
        for idx, channel_index in enumerate(channel_list):
            if len(f.readSignal(channel_index)) == max_len:
                sigbufs[idx, :] = f.readSignal(channel_index)
        return sigbufs


if __name__ == "__main__":
    start = time.time()
    args = parser.parse_args()
    paths = get_paths()
    data_dict = get_data_dictionary(paths['parent'], args.dict_string)

    num_eegs = (len([item for sublist in data_dict.values() for item in sublist]))
    print(f'Number of EEGs: {num_eegs}')
    label_file_string = f"{paths['parent']}/{args.dict_string.strip('.json')}_labels.csv" 
    print(f"Label Location: {label_file_string}")
    ## process eegs (multiprocessing)
    
    H_VALUES = (12,24,48,64,96)
    W_VALUES = (1,2,4,6,8)
    O_VALUES = (25,50,75)
    
    label_dict = collections.defaultdict()
    for key, entries in data_dict.items():
        for observation in entries:
            eeg = get_eeg(observation)
            for h in H_VALUES:
                down_sampled_eeg = down_sample_eeg(eeg, observation, h)
                for w, o in list(itertools.product(W_VALUES, O_VALUES)):
                    #process_eeg(down_sampled_eeg, key, observation, h, w, o,label_dict, paths['image']) 
                    p = multiprocessing.Process(target = process_eeg, args=(down_sampled_eeg, key, observation, h, w, o,
                            label_dict, paths['image'])) 
                    p.start()
    with csv.writer(open(label_file_string,'w')) as f:
        for key, value in label_dict.items():
            f.writerow([key, value])
    end = time.time()
    print(f"Time: {end-start}")
