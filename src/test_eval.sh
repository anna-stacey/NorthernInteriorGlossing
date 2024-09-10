WHOLE_INPUT=./src/test_data/test.txt
INPUT=./src/test_data/test.input
OUTPUT=./src/test_data/test_fairseq.output
GOLD_OUTPUT=./src/test_data/test.output
RESULTS_CSV=./seg_results.csv
EXPECTED_RESULTS="100.0%,None,None,None,None,,"

python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT --output_file=$OUTPUT --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT
python3 src/test_eval.py --results_csv=$RESULTS_CSV --expected_results=$EXPECTED_RESULTS