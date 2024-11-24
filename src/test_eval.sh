SEG_RESULTS_CSV=./seg_results.csv
GLOSS_RESULTS_CSV=./gloss_results.csv
PIPELINE_RESULTS_CSV=./pipeline_results.csv
SEG_LINE_NUMBER=2
GLOSS_LINE_NUMBER=3

# No gold boundaries, no predicted boundaries, 100% correct, no words OOV
WHOLE_INPUT_1=./src/test_data/test_1.txt
INPUT_1=./src/test_data/test_1.input
TRAIN_INPUT_1=./src/test_data/test_1.input
OUTPUT_1=./src/test_data/test_fairseq_1.output
GOLD_OUTPUT_1=./src/test_data/test_1.output
EXPECTED_RESULTS_1="100.00%,None,None,None,None,None,None,None,0.00%,None"

# No gold boundaries, no predicted boundaries, 0% correct, all words OOV
WHOLE_INPUT_2=./src/test_data/test_1.txt
INPUT_2=./src/test_data/test_1.input
TRAIN_INPUT_2=./src/test_data/test_2_train.input
OUTPUT_2=./src/test_data/test_fairseq_2.output
GOLD_OUTPUT_2=./src/test_data/test_2.output
EXPECTED_RESULTS_2="0.00%,None,None,None,None,None,None,None,100.00%,0.00%"

# Gold boundaries, no predicted boundaries, 0% correct
WHOLE_INPUT_3=./src/test_data/test_3.txt
INPUT_3=./src/test_data/test_1.input
OUTPUT_3=./src/test_data/test_fairseq_3.output
GOLD_OUTPUT_3=./src/test_data/test_3.output
EXPECTED_RESULTS_3="0.00%,None,0.00%,0.00%,None,0.00%,0.00%,0.00%,None,None"

# Gold boundaries, predicted boundaries, 100% correct
WHOLE_INPUT_4=./src/test_data/test_3.txt
INPUT_4=./src/test_data/test_1.input
OUTPUT_4=./src/test_data/test_fairseq_4.output
GOLD_OUTPUT_4=./src/test_data/test_3.output
EXPECTED_RESULTS_4="100.00%,100.00%,100.00%,100.00%,100.00%,100.00%,100.00%,100.00%,None,None"

# Gold boundaries, predicted boundaries, 0% correct
# Type-insensitive and type-sensitive: TP: i, FP: iii, FN: iii
WHOLE_INPUT_5=./src/test_data/test_3.txt
INPUT_5=./src/test_data/test_1.input
OUTPUT_5=./src/test_data/test_fairseq_5.output
GOLD_OUTPUT_5=./src/test_data/test_3.output
EXPECTED_RESULTS_5="0.00%,25.00%,25.00%,25.00%,25.00%,25.00%,25.00%,100.00%,None,None"

# Gold boundaries, predicted boundaries, 0% correct
# Type-insensitive and type-sensitive: TP: i, FP: ii, FN: iii
WHOLE_INPUT_6=./src/test_data/test_3.txt
INPUT_6=./src/test_data/test_1.input
OUTPUT_6=./src/test_data/test_fairseq_6.output
GOLD_OUTPUT_6=./src/test_data/test_3.output
EXPECTED_RESULTS_6="0.00%,33.33%,25.00%,28.57%,33.33%,25.00%,28.57%,75.00%,None,None"

# Gold boundaries and predicted boundaries
# Specially looking at diff. boundary types and words with mulitple boundaries
# Partly OOV
# P.S. This numbering system is terrible to update.  Switching to animals.
WHOLE_INPUT_TIGER=./src/test_data/test_21.txt
INPUT_TIGER=./src/test_data/test_1.input
TRAIN_INPUT_TIGER=./src/test_data/test_21_train.input
OUTPUT_TIGER=./src/test_data/test_fairseq_21.output
GOLD_OUTPUT_TIGER=./src/test_data/test_21.output
# If we do the skip boundaries approach
# And be boundary-type *insensitive*
# And assume each infix boundary counts separately
# Type-insensitive: TP: iiiiiii, FP: ii, FN: iiii
# Type-sensitive: TP: iiiiii FP: iii FN: iiiii
EXPECTED_RESULTS_TIGER="0.00%,77.78%,63.64%,70.00%,66.67%,54.55%,60.00%,81.82%,50.00%,0.00%"

# Gold all grams, predicted all grams, all wrong
GOLD_7=./src/test_data/test_1.txt
OUTPUT_7=./src/test_data/test_7_pred.txt
EXPECTED_RESULTS_7="0.00%,0.00%,None,0.00%"

# Gold all grams, predicted all stems, all wrong
GOLD_8=./src/test_data/test_1.txt
OUTPUT_8=./src/test_data/test_9_pred.txt
EXPECTED_RESULTS_8="0.00%,0.00%,0.00%,None"

# All grams, all correct
GOLD_9=./src/test_data/test_1.txt
OUTPUT_9=./src/test_data/test_1.txt
EXPECTED_RESULTS_9="100.00%,100.00%,None,100.00%"

# Gold all stems, predicted all stems, all wrong
GOLD_10=./src/test_data/test_10.txt
OUTPUT_10=./src/test_data/test_9_pred.txt
EXPECTED_RESULTS_10="0.00%,0.00%,0.00%,None"

# Gold all stems, predicted all grams, all wrong
GOLD_11=./src/test_data/test_10.txt
OUTPUT_11=./src/test_data/test_7_pred.txt
EXPECTED_RESULTS_11="0.00%,0.00%,None,0.00%"

# All stems, all correct
GOLD_12=./src/test_data/test_10.txt
OUTPUT_12=./src/test_data/test_10.txt
EXPECTED_RESULTS_12="100.00%,100.00%,100.00%,None"

# Gold all stems, predicted all stems, partly correct
# 3 correct stems, 1 incorrect stem, no grams
GOLD_13=./src/test_data/test_10.txt
OUTPUT_13=./src/test_data/test_13_pred.txt
EXPECTED_RESULTS_13="75.00%,75.00%,75.00%,None"

# Gold all stems, predicted mixed stems/grams, partly correct
# 2 correct stems, 1 incorrect stem, 1 incorrect gram
GOLD_14=./src/test_data/test_10.txt
OUTPUT_14=./src/test_data/test_14_pred.txt
EXPECTED_RESULTS_14="50.00%,50.00%,66.67%,0.00%"

# Moving into multi-morphemic words
# Mixed stems/grams, all correct
GOLD_15=./src/test_data/test_3.txt
OUTPUT_15=./src/test_data/test_3.txt
EXPECTED_RESULTS_15="100.00%,100.00%,100.00%,100.00%"

# Mixed stems/grams, partly correct
# 2 correct stems, 1 incorrect stem, 3 correct grams, 2 incorrect grams
GOLD_16=./src/test_data/test_3.txt
OUTPUT_16=./src/test_data/test_16_pred.txt
EXPECTED_RESULTS_16="62.50%,50.00%,66.67%,60.00%"

# Mixed stems/grams, glosses correct but seg mistakes, (incl. boundary-only mistakes), no OOV words
GOLD_17=./src/test_data/test_3.txt
INPUT_17=./src/test_data/test_1.input
TRAIN_INPUT_17=./src/test_data/test_1.input
OUTPUT_17=./src/test_data/test_17_pred.txt
EXPECTED_RESULTS_17="100.00%,100.00%,50.00%,0.00%,None"

# Mixed stems/grams, glosses correct but seg mistakes, (incl. boundary-only mistakes), no OOV words
# 6/8 morphemes correct (7/8 BoW), 2/4 stems correct, 4/5 grams correct
GOLD_18=./src/test_data/test_3.txt
INPUT_18=./src/test_data/test_1.input
TRAIN_INPUT_18=./src/test_data/test_1.input
OUTPUT_18=./src/test_data/test_18_pred.txt
EXPECTED_RESULTS_18="75.00%,87.50%,0.00%,0.00%,None"

# Mixed stems/grams
# 2/4 morphemes correct (4/4 BoW), 1/3 stems correct, 1/3 grams correct, all words OOV
GOLD_19=./src/test_data/test_11.txt
INPUT_19=./src/test_data/test_1.input
TRAIN_INPUT_19=./src/test_data/test_2_train.input
OUTPUT_19=./src/test_data/test_19_pred.txt
EXPECTED_RESULTS_19="50.00%,100.00%,50.00%,100.00%,50.00%"

# Mixed stems/grams
# 4/7 morphemes correct (6/7 BoW), 3/5 stems correct, 1/2 grams correct, half OOV
GOLD_20=./src/test_data/test_20.txt
OUTPUT_20=./src/test_data/test_20_pred.txt
INPUT_20=./src/test_data/test_1.input
TRAIN_INPUT_20=./src/test_data/test_21_train.input
EXPECTED_RESULTS_20="57.14%,85.71%,50.00%,50.00%,0.00%"

echo "Segmentation Test 1:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_1 --output_file=$OUTPUT_1 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_1 --train_input_file=$TRAIN_INPUT_1 --test_input_file=$INPUT_1 > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_1

echo "Segmentation Test 2:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_2 --output_file=$OUTPUT_2 --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_2 --train_input_file=$TRAIN_INPUT_2 --test_input_file=$INPUT_2 > /dev/null
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

echo "Segmentation Test 7:"
python3 src/test_seg.py --whole_input_file=$WHOLE_INPUT_TIGER --output_file=$OUTPUT_TIGER --output_file_is_fairseq_formatted --gold_output_file=$GOLD_OUTPUT_TIGER --train_input_file=$TRAIN_INPUT_TIGER --test_input_file=$INPUT_TIGER > /dev/null
python3 src/test_eval.py --results_csv=$SEG_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_TIGER

echo "Gloss Test 1:"
python3 src/eval_gloss.py --test_file=$GOLD_7 --output_file=$OUTPUT_7 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_7

echo "Gloss Test 2:"
python3 src/eval_gloss.py --test_file=$GOLD_8 --output_file=$OUTPUT_8 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_8

echo "Gloss Test 3:"
python3 src/eval_gloss.py --test_file=$GOLD_9 --output_file=$OUTPUT_9 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_9

echo "Gloss Test 4:"
python3 src/eval_gloss.py --test_file=$GOLD_10 --output_file=$OUTPUT_10 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_10

echo "Gloss Test 5:"
python3 src/eval_gloss.py --test_file=$GOLD_11 --output_file=$OUTPUT_11 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_11

echo "Gloss Test 6:"
python3 src/eval_gloss.py --test_file=$GOLD_12 --output_file=$OUTPUT_12 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_12

echo "Gloss Test 7:"
python3 src/eval_gloss.py --test_file=$GOLD_13 --output_file=$OUTPUT_13 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_13

echo "Gloss Test 8:"
python3 src/eval_gloss.py --test_file=$GOLD_14 --output_file=$OUTPUT_14 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_14

echo "Gloss Test 9:"
python3 src/eval_gloss.py --test_file=$GOLD_15 --output_file=$OUTPUT_15 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_15

echo "Gloss Test 10:"
python3 src/eval_gloss.py --test_file=$GOLD_16 --output_file=$OUTPUT_16 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER > /dev/null
python3 src/test_eval.py --results_csv=$GLOSS_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_16

echo "Pipeline Test 1:"
python3 src/eval_pipeline.py --test_file=$GOLD_17 --output_file=$OUTPUT_17 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER --train_input_file=$TRAIN_INPUT_17 --test_input_file=$INPUT_17 > /dev/null
python3 src/test_eval.py --results_csv=$PIPELINE_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_17

echo "Pipeline Test 2:"
python3 src/eval_pipeline.py --test_file=$GOLD_18 --output_file=$OUTPUT_18 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER --train_input_file=$TRAIN_INPUT_18 --test_input_file=$INPUT_18  > /dev/null
python3 src/test_eval.py --results_csv=$PIPELINE_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_18

echo "Pipeline Test 3:"
python3 src/eval_pipeline.py --test_file=$GOLD_19 --output_file=$OUTPUT_19 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER --train_input_file=$TRAIN_INPUT_19 --test_input_file=$INPUT_19 > /dev/null
python3 src/test_eval.py --results_csv=$PIPELINE_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_19

echo "Pipeline Test 4:"
python3 src/eval_pipeline.py --test_file=$GOLD_20 --output_file=$OUTPUT_20 --segmentation_line_number=$SEG_LINE_NUMBER --gloss_line_number=$GLOSS_LINE_NUMBER --train_input_file=$TRAIN_INPUT_20 --test_input_file=$INPUT_20 > /dev/null
python3 src/test_eval.py --results_csv=$PIPELINE_RESULTS_CSV --expected_results=$EXPECTED_RESULTS_20
