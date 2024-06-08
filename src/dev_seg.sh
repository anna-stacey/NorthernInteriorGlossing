#!/bin/bash

WHOLE_INPUT=data/dev.txt
INPUT=generated_data/dev.input
OUTPUT=generated_data/dev_fairseq.output
GOLD_OUTPUT=generated_data/dev.output
TRAIN_OUTPUT=generated_data/train.output

# To run on the unsegmenting baseline, set output_file=$INPUT and don't use the fairseq flag
cat $INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $OUTPUT
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT --output_file=$OUTPUT --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT --train_output_file=$TRAIN_OUTPUT