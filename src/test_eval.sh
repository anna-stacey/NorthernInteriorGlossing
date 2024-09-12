RESULTS_CSV=./seg_results.csv

# No gold boundaries, no predicted boundaries, 100% correct
WHOLE_INPUT_1=./src/test_data/test_1.txt
INPUT_1=./src/test_data/test_1.input
OUTPUT_1=./src/test_data/test_fairseq_1.output
GOLD_OUTPUT_1=./src/test_data/test_1.output
EXPECTED_RESULTS_1="100.0%,None,None,None,None,None,None"

# No gold boundaries, no predicted boundaries, 0% correct
WHOLE_INPUT_2=./src/test_data/test_1.txt
INPUT_2=./src/test_data/test_1.input
OUTPUT_2=./src/test_data/test_fairseq_2.output
GOLD_OUTPUT_2=./src/test_data/test_2.output
EXPECTED_RESULTS_2="0.0%,None,None,None,None,None,None"

# Gold boundaries, no predicted boundaries, 0% correct
WHOLE_INPUT_3=./src/test_data/test_3.txt
INPUT_3=./src/test_data/test_1.input
OUTPUT_3=./src/test_data/test_fairseq_3.output
GOLD_OUTPUT_3=./src/test_data/test_3.output
EXPECTED_RESULTS_3="0.0%,None,0.0%,0.0%,0.0%,None,None"

python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_1 --output_file=$OUTPUT_1 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_1
python3 src/test_eval.py --results_csv=$RESULTS_CSV --expected_results=$EXPECTED_RESULTS_1

python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_2 --output_file=$OUTPUT_2 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_2
python3 src/test_eval.py --results_csv=$RESULTS_CSV --expected_results=$EXPECTED_RESULTS_2

python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_3 --output_file=$OUTPUT_3 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_3
python3 src/test_eval.py --results_csv=$RESULTS_CSV --expected_results=$EXPECTED_RESULTS_3
