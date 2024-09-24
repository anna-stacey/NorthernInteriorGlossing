SEG_RESULTS_CSV=./seg_results.csv
GLOSS_RESULTS_CSV=./gloss_results.csv
SEG_LINE_NUMBER=2
GLOSS_LINE_NUMBER=3

# No gold boundaries, no predicted boundaries, 100% correct
WHOLE_INPUT_1=./src/test_data/test_1.txt
INPUT_1=./src/test_data/test_1.input
OUTPUT_1=./src/test_data/test_fairseq_1.output
GOLD_OUTPUT_1=./src/test_data/test_1.output
EXPECTED_RESULTS_1="100.00%,None,None,None,None,None,None"

# No gold boundaries, no predicted boundaries, 0% correct
WHOLE_INPUT_2=./src/test_data/test_1.txt
INPUT_2=./src/test_data/test_1.input
OUTPUT_2=./src/test_data/test_fairseq_2.output
GOLD_OUTPUT_2=./src/test_data/test_2.output
EXPECTED_RESULTS_2="0.00%,None,None,None,None,None,None"

# Gold boundaries, no predicted boundaries, 0% correct
WHOLE_INPUT_3=./src/test_data/test_3.txt
INPUT_3=./src/test_data/test_1.input
OUTPUT_3=./src/test_data/test_fairseq_3.output
GOLD_OUTPUT_3=./src/test_data/test_3.output
EXPECTED_RESULTS_3="0.00%,None,0.00%,0.00%,0.00%,None,None"

# Gold boundaries, predicted boundaries, 100% correct
WHOLE_INPUT_4=./src/test_data/test_3.txt
INPUT_4=./src/test_data/test_1.input
OUTPUT_4=./src/test_data/test_fairseq_4.output
GOLD_OUTPUT_4=./src/test_data/test_3.output
EXPECTED_RESULTS_4="100.00%,100.00%,100.00%,100.00%,100.00%,None,None"

# Gold boundaries, predicted boundaries, 0% correct
# TP: i, FP: iii, FN: iii
WHOLE_INPUT_5=./src/test_data/test_3.txt
INPUT_5=./src/test_data/test_1.input
OUTPUT_5=./src/test_data/test_fairseq_5.output
GOLD_OUTPUT_5=./src/test_data/test_3.output
EXPECTED_RESULTS_5="0.00%,25.00%,25.00%,25.00%,100.00%,None,None"

# Gold boundaries, predicted boundaries, 0% correct
# TP: i, FP: ii, FN: iii
WHOLE_INPUT_6=./src/test_data/test_3.txt
INPUT_6=./src/test_data/test_1.input
OUTPUT_6=./src/test_data/test_fairseq_6.output
GOLD_OUTPUT_6=./src/test_data/test_3.output
EXPECTED_RESULTS_6="0.00%,33.33%,25.00%,28.57%,75.00%,None,None"

# All grams, all wrong
GOLD_7=./src/test_data/test_1.txt
OUTPUT_7=./src/test_data/test_7_pred.txt
EXPECTED_RESULTS_7="0.00%,0.00%,None,0.00%"

# All grams, all correct
GOLD_8=./src/test_data/test_1.txt
OUTPUT_8=./src/test_data/test_1.txt
EXPECTED_RESULTS_8="100.00%,100.00%,None,100.00%"

echo "Segmentation Test 1:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_1 --output_file=$OUTPUT_1 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_1 > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_1

echo "Segmentation Test 2:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_2 --output_file=$OUTPUT_2 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_2 > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_2

echo "Segmentation Test 3:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_3 --output_file=$OUTPUT_3 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_3 > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_3

echo "Segmentation Test 4:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_4 --output_file=$OUTPUT_4 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_4 > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_4

echo "Segmentation Test 5:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_5 --output_file=$OUTPUT_5 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_5 > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_5

echo "Segmentation Test 6:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_6 --output_file=$OUTPUT_6 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_6 > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_6

echo "Gloss Test 1:"
python3 src/eval_gloss.py --test_file=$GOLD_7 --output_file=$OUTPUT_7 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_7

echo "Gloss Test 2:"
python3 src/eval_gloss.py --test_file=$GOLD_8 --output_file=$OUTPUT_8 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_8
