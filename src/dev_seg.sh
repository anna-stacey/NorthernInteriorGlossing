#!/bin/bash

INPUT=dev.input
OUTPUT=dev_fairseq.output
GOLD_OUTPUT=dev.output

cat $INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $OUTPUT
python3 src/test_seg.py --output_file=$OUTPUT --gold_output_file=$GOLD_OUTPUT