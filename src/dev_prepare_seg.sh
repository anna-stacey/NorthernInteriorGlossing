#!/bin/bash

TRAIN_SET=generated_data/train.txt
DEV_SET=generated_data/dev.txt
TEST_SET=generated_data/test.txt
PIPELINE_SET=generated_data/dev.txt

# Prepare the data for fairseq
python3 src/preprocess_seg.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET --pipeline_file=$PIPELINE_SET
fairseq-preprocess --source-lang input --target-lang output --trainpref train --validpref dev --destdir data-bin/
# Train fairseq
sh src/train_seg.sh 