#!/bin/bash
SEG_INPUT=generated_data/pipeline.input
SEG_OUTPUT=generated_data/pipeline_fairseq.output
GLOSS_TRAIN_SET=data/train.txt
GLOSS_DEV_SET=data/dev.txt
GLOSS_TEST_SET=data/dev.txt
SEG_LINE_NUMBER=2
GLOSS_LINE_NUMBER=3 # 3 for St̓át̓imcets, 4 for Gitksan

# Run the segmentation
cat $SEG_INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $SEG_OUTPUT  
# Run the glossing
python3 src/pipeline.py --seg_output_file=$SEG_OUTPUT --gloss_train_file=$GLOSS_TRAIN_SET --gloss_dev_file=$GLOSS_DEV_SET --gloss_test_file=$GLOSS_TEST_SET --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER