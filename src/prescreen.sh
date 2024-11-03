#!/bin/bash

TRAIN_SET=data/train.txt
DEV_SET=data/dev.txt
TEST_SET=data/test.txt
SEG_LINE_NUMBER=2 # 2 for all else, 3 for Secwepemctsín
GLOSS_LINE_NUMBER=3 # 3 for Nɬeʔkepmxcín and St̓át̓imcets, 4 for Gitksan and Secwepemctsín
python3 src/prescreen_data.py --do_screen_data --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER
