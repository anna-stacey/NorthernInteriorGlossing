#!/bin/bash

WHOLE_INPUT=data/test.txt
INPUT=generated_data/test.input
OUTPUT=generated_data/test_fairseq.output
GOLD_OUTPUT=generated_data/test_gold.output
TRAIN_OUTPUT=generated_data/train.output

cat $INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $OUTPUT
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT --output_file=$OUTPUT --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT --train_output_file=$TRAIN_OUTPUT