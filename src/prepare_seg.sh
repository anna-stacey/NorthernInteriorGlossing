#!/bin/bash

TRAIN_SET=train.txt
DEV_SET=dev.txt
TEST_SET=test.txt

# Prepare the data for fairseq
python3 preprocess_seg.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET
fairseq-preprocess --source-lang input --target-lang output --trainpref train --validpref dev --destdir data-bin/
# Train fairseq
sh train_seg.sh 