#!/bin/bash

TRAIN_SET=data/train.txt
DEV_SET=data/dev.txt
TEST_SET=data/dev.txt
OUTPUT_FOLDER="generated_data/"
OUTPUT_FILE="gloss_pred.txt"
SEG_LINE_NUMBER=2 # 2 for all else, 3 for Secwepemctsín
GLOSS_LINE_NUMBER=3 # 3 for Nɬeʔkepmxcín and St̓át̓imcets, 4 for Gitksan and Secwepemctsín
python3 src/gloss.py --train_file=$TRAIN_SET --dev_file=$DEV_SET --test_file=$TEST_SET --output_folder=$OUTPUT_FOLDER --output_file=$OUTPUT_FILE --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER
python3 src/eval_gloss.py --test_file=$TEST_SET --output_file=$OUTPUT_FOLDER$OUTPUT_FILE --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER
rm ./stem_dict.txt