#!/bin/bash
# From prepare_seg.sh
TRAIN_SET=train.txt
DEV_SET=dev.txt
TEST_SET=test.txt
PIPELINE_SET=dev.txt

# Prepare the data for fairseq
python3 preprocess_seg.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET --pipeline_file=$PIPELINE_SET

# From run_pipeline.sh
SEG_INPUT=pipeline.input
SEG_OUTPUT=pipeline_fairseq.output
DATA_SUMMARY=pipeline_data_summary.txt
GLOSS_TRAIN_SET=train.txt
GLOSS_DEV_SET=dev.txt
GLOSS_TEST_SET=dev.txt
# GOLD_OUTPUT=test_gold.output

# Run the segmentation
cat $SEG_INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $SEG_OUTPUT  
# Run the glossing
python3 pipeline.py --seg_output_file=$SEG_OUTPUT --data_summary_file=$DATA_SUMMARY --gloss_train_file=$GLOSS_TRAIN_SET --gloss_dev_file=$GLOSS_DEV_SET --gloss_test_file=$GLOSS_TEST_SET