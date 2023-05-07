#!/bin/bash

TRAIN_SET=train.txt
DEV_SET=dev.txt
TEST_SET=dev.txt
python3 src/gloss.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET