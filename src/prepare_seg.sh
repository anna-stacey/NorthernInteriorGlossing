#!/bin/bash

TRAIN_SET=data/train.txt
DEV_SET=data/dev.txt
TEST_SET=data/test.txt

# Prepare the data for fairseq
python3 src/preprocess_seg.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET
fairseq-preprocess --source-lang input --target-lang output --trainpref generated_data/train --validpref generated_data/dev --destdir data-bin/
# Train fairseq
sh src/train_seg.sh 