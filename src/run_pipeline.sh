#!/bin/bash
INPUT=test_for_pipeline.input
OUTPUT=test_for_pipeline_fairseq.output
DATA_SUMMARY=test_data_summary.txt
# GOLD_OUTPUT=test_gold.output

cat $INPUT | fairseq-interactive --path models/checkpoint_best.pt data-bin > $OUTPUT  
python3 pipeline.py --seg_output_file=$OUTPUT --data_summary_file=$DATA_SUMMARY