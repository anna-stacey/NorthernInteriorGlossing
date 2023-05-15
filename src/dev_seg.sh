#!/bin/bash

INPUT=generated_data/dev.input
OUTPUT=generated_data/dev_fairseq.output
GOLD_OUTPUT=generated_data/dev.output

cat $INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $OUTPUT
python3 src/test_seg.py --output_file=$OUTPUT --gold_output_file=$GOLD_OUTPUT