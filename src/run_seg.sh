#!/bin/bash

WHOLE_INPUT=data/test.txt
INPUT=generated_data/test.input
OUTPUT=generated_data/test_fairseq.output
GOLD_OUTPUT=generated_data/test_gold.output

cat $INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $OUTPUT
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT --output_file=$OUTPUT --gold_output_file=$GOLD_OUTPUT