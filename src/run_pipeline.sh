#!/bin/bash
SEG_INPUT=pipeline.input
SEG_OUTPUT=pipeline_fairseq.output
DATA_SUMMARY=pipeline_data_summary.txt
GLOSS_TRAIN_SET=train.txt
GLOSS_DEV_SET=dev.txt
GLOSS_TEST_SET=test.txt
# GOLD_OUTPUT=test_gold.output

# Run the segmentation
cat $SEG_INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $SEG_OUTPUT  
# Run the glossing
python3 src/pipeline.py --seg_output_file=$SEG_OUTPUT --data_summary_file=$DATA_SUMMARY --gloss_train_file=$GLOSS_TRAIN_SET --gloss_dev_file=$GLOSS_DEV_SET --gloss_test_file=$GLOSS_TEST_SET