#!/bin/bash
SEG_PREDICTIONS=generated_data/seg_pred.txt
GLOSS_TRAIN_SET=data/train.txt
GLOSS_DEV_SET=data/dev.txt
GLOSS_TEST_SET=data/dev.txt
OUTPUT_FOLDER="generated_data/"
OUTPUT_FILE="pipeline_pred.txt"
TEST_INPUT=generated_data/test.input
TRAIN_INPUT=generated_data/train.input
SEG_LINE_NUMBER=2 # 2 for all else, 3 for Secwepemctsín
GLOSS_LINE_NUMBER=3 # 3 for Nɬeʔkepmxcín and St̓át̓imcets, 4 for Gitksan and Secwepemctsín

# The seg predictions used come from running the segmenter first
# Now, run the glosser on those predictions
python3 src/pipeline.py --seg_pred_file=$SEG_PREDICTIONS --gloss_train_file=$GLOSS_TRAIN_SET --gloss_dev_file=$GLOSS_DEV_SET --gloss_test_file=$GLOSS_TEST_SET --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER
python3 src/eval_pipeline.py --test_file=$GLOSS_TEST_SET --output_file=$OUTPUT_FOLDER$OUTPUT_FILE --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER --train_input_file=$TRAIN_INPUT --test_input_file=$TEST_INPUT
