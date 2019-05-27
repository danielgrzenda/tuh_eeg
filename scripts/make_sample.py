#!/usr/bin/env python3


import argparse
import collections
import json
import numpy as np
import operator
import os
from pathlib import Path
import random


# argpare arguments

def get_paths():
    here = Path(f'{os.getcwd()}')
    parent_path = here.parent
    data_path = parent_path/'data'
    test_path = data_path/'augmented/test'
    img_path = data_path/'images/test'
    return parent_path, test_path, img_path

def get_data_dictionary(parent_path):
    with open(parent_path/'data_dict.json','r') as f:
        data_dict = json.load(f)
    return data_dict


def sample_data_by_label(data_dict, sample_rate):
    label_dict = data_to_label_dict(data_dict)
    sample = collections.defaultdict(list)
    for key, entries in label_dict.items():
        total_for_this_label = 0
        for observation in entries:
            if np.random.binomial(1, p=sample_rate) == 1:
                sample[key].append(observation)
                total_for_this_label += 1
        if total_for_this_label <= 0:
            sample[key ].append(random.choice(entries))
    data_dict = label_to_data_dict(sample)
    return data_dict


def label_to_data_dict(label_dict):
    data_dict = collections.defaultdict(list)
    for key, entries in label_dict.items():
        for observation in entries:
            data_dict[observation['patient']].append(observation)
    return data_dict


def data_to_label_dict(data_dict):
    label_dict = collections.defaultdict(list)
    for key, entries in data_dict.items():
        for observation in entries:
            label_set = frozenset(observation['labels'])
            label_dict[label_set].append(observation)
    return label_dict


def get_time_breakdown(data_dict):
    time_breakdown = collections.defaultdict(list)
    for key, value in data_dict.items():
        for entry in value:
            time_list = zip(entry['labels'], entry['durations'])
            last = 0
            for label, curr in time_list:
                time = float(curr) - last
                time_breakdown[label].append(time)
                last = float(curr)
    
    summary = collections.defaultdict()
    for key, value in time_breakdown.items():
        summary[key] = sum(value)
    
    total = sum(summary.values())
    print(f'Total Time: {total}')
    for key, value in sorted(summary.items(), key=operator.itemgetter(1), reverse=True):
        print(f'{key} {(value/total)*100:.2f}%')


def save_sample(parent_path, sample_dict):
    with open(parent_path/'sample_dict.json', 'w') as f:
        f.write(json.dumps(sample_dict))


if __name__ == "__main__":
    parent_path, test_path, img_path = get_paths()
    data_dict = get_data_dictionary(parent_path)
    sample_eegs = sample_data_by_label(data_dict, 0.01)
    get_time_breakdown(sample_eegs)
    save_sample(parent_path, sample_eegs)

