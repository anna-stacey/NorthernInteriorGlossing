#!/bin/bash

WHOLE_INPUT=data/dev.txt
INPUT=generated_data/dev.input
OUTPUT=generated_data/dev_fairseq.output
GOLD_OUTPUT=generated_data/dev.output
TRAIN_OUTPUT=generated_data/train.output
SEED_COUNT=9 # Starts at 0 so you'll use n + 1 models (e.g. if this is 9, you'll get an ensemble run from 10 models)
EPOCHS_TO_USE=_best # You can set this to "_best" or a number
# No separating colon before the first model name
MODELS="models_seed0/checkpoint"$EPOCHS_TO_USE".pt"
for i in $(seq 1 1 $SEED_COUNT); do MODELS=$MODELS":models_seed"$i"/checkpoint"$EPOCHS_TO_USE".pt"; done
echo "Using model(s): "$MODELS

# To run on the unsegmenting baseline, set output_file=$INPUT and don't use the fairseq flag
cat $INPUT | fairseq-interactive --path $MODELS data-bin > $OUTPUT
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT --output_file=$OUTPUT --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT --train_output_file=$TRAIN_OUTPUT