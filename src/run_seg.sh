#!/bin/bash

INPUT=test.input
OUTPUT=test_fairseq.output
GOLD_OUTPUT=test_gold.output

cat $INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $OUTPUT
python3 test_seg.py --output_file=$OUTPUT --gold_output_file=$GOLD_OUTPUT