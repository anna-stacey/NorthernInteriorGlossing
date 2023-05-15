#!/bin/bash

TRAIN_SET=generated_data/train.txt
DEV_SET=generated_data/dev.txt
TEST_SET=generated_data/test.txt
python3 src/gloss.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET