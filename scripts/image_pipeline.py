#!/usr/bin/env python3


import argparse
import json
from pyspark import SparkConf, SparkContext


def get_rdd(data_dict):
    list_of_entries = []
    for key, value in data_dict.items():
        if key == '00004151':
            for entry in value:
                list_of_entries.append(entry)
    return sc.parallelize(list_of_entries)


def load_data_dict(filename):
    with open(filename, 'r') as f:
        data_dict = json.load(f)
    return data_dict 


def start_spark():
    conf = (SparkConf().setMaster("local")
            .setAppName("EEG to Image"))
    sc = SparkContext(conf=conf)
    return sc, conf


def get_args():
    parser = argparse.ArgumentParser(description="Process EEGs to get Images")
    parser.add_argument('filename', metavar='N', type=str, help='string for the\
                                            filename of the data dictionary')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    sc, conf = start_spark()
    data_dict = load_data_dict(args.filename)
    rdd = get_rdd(sc, data_dict)
    for x in rdd.collect()[:5]:
        print(x)


