#!/bin/bash

TRAIN_SET=data/train.txt
DEV_SET=data/dev.txt
TEST_SET=data/dev.txt
SEG_LINE_NUMBER=2
GLOSS_LINE_NUMBER=3 # 3 for St̓át̓imcets, 4 for Gitksan
#python3 src/prescreen_data.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER
python3 src/gloss.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER