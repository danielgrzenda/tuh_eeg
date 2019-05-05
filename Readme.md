# SeizureNet

## Table of Contents
<!-- vim-markdown-toc GFM -->

* [Introduction](#introduction)
* [Directory Structure](#directory-structure)
* [TODO](#todo)

<!-- vim-markdown-toc -->

## Introduction

The goal of this repo is to replicate and then improve upon the multi-class
seizure classification problem described in [this
paper](https://arxiv.org/pdf/1903.03232.pdf). The data we are using for this
comes from the TUH EEG corpus online. It can be found
[here](https://www.isip.piconepress.com/projects/tuh_eeg/). Notebook `00` in
this repo will download it for you.
 
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

* Build the image creation script for the small `test` set.
* Run the whole pipeline for the entire dataset
    * A little nervous about the size of the final directory 
* Worry about the validation split (by patient, session, etc?)
* Try out different techniques
    * Other down-sampling techniques
    * Alternatives to the fft (rfft, gramian angular field, wavelet)
    * Down sample less than 96


