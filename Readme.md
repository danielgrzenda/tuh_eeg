# SeizureNet

## Table of Contents
<!-- vim-markdown-toc GFM -->

* [Introduction](#introduction)
* [Getting Started](#getting-started)
* [Directory Structure](#directory-structure)
* [TODO](#todo)

<!-- vim-markdown-toc -->

## Introduction

The goal of this repo is to replicate and then improve upon the multi-class
seizure classification problem described in [this
paper](https://arxiv.org/pdf/1903.03232.pdf). The data we are using for this
comes from the TUH EEG corpus online. It can be found
[here](https://www.isip.piconepress.com/projects/tuh_eeg/). The data directory
is not sourced controled on Github, but see the [Getting
Started](#getting-started) section for directions on how to download it.
 
## Getting Started 

The first thing to do is build out the data directory. Be sure to check the free
space on your computer, as the raw data requires ~56 GB. To download the data run
`/nbs/00_get_data.ipynb`. Then to build the data dictionary used for exploring
the raw data set and building out the image data set, run the
`/nbs/01_data_dict.ipynb` notebook. 

## Directory Structure

* /nbs - all the notebook for exploring/building out the data pipeline
* /data
    * /raw - where the data got unzipped to. Follows `TUH EEG` format.
    * /augmented - where the sampled data was saved
        * /train_val
        * /test
    * /images - where image transforms of the 
* /their_readme.txt - the readme from `TUH EEG` describing the data/eeg
  technology
* /data_dict.json - the data dictionary (generated in nbs) for ease of
  work/summary of the data
* /aug_labels.csv - a label file where each row is (path, label) for all files
  in the augmented directory
* /img_labels.csv - a label file where each row is (path, label) for all files
  in the images directory

## TODO

* combine and sparkify the sampling/image creation nbs
* run the pipeline script for the small `test` set.
* Run the whole pipeline for the entire dataset
    * A little nervous about the size of the final directory (~11TB?)
* Worry about the validation split (by patient, session, etc?)
* Try out different techniques
    * Other down-sampling techniques
    * Alternatives to the fft (rfft, gramian angular field, wavelet)
    * Down sample less than 96

