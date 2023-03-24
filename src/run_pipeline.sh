#!/bin/bash
SEG_INPUT=test_for_pipeline.input
SEG_OUTPUT=test_for_pipeline_fairseq.output
DATA_SUMMARY=test_data_summary.txt
GLOSS_TRAIN_SET=train.txt
GLOSS_DEV_SET=dev.txt
GLOSS_TEST_SET=test.txt
# GOLD_OUTPUT=test_gold.output

cat $SEG_INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $SEG_OUTPUT  
python3 pipeline.py --seg_output_file=$SEG_OUTPUT --data_summary_file=$DATA_SUMMARY --gloss_train_file=$GLOSS_TRAIN_SET --gloss_dev_file=$GLOSS_DEV_SET --gloss_test_file=$GLOSS_TEST_SET