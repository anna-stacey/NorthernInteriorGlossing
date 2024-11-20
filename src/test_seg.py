import click
from os import path
import re
from gloss import make_sentence_list_with_prediction
from glossed_data_handling_utilities import  REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, LANG_LABEL_REGEX
from glossed_data_utilities import add_back_OOL_words, as_percent, print_results_csv, read_file, create_file_of_sentences, OUT_OF_LANGUAGE_MARKER

OUTPUT_DIR = "generated_data/"
GOLD_OUTPUT_FILE_NAME = "seg_gold.txt"
PRED_OUTPUT_FILE_NAME = "seg_pred.txt"
ALL_BOUNDARIES = [LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY]
OUTPUT_CSV = "./seg_results.csv"
OUTPUT_CSV_HEADER = "Acc,Boundary Prec,B Recall,B F1,B Count,OOV Count,OOV Acc"
DO_PRINT_RESULTS_CSV = True
NO_RESULT_MARKER = None

# Returns a list of lines in the file, "\n" within the line removed
def read_lines_from_file(file_path):
    with open(file_path) as f:
        lines = f.readlines()

    formatted_lines = []
    for line in lines:
        line = line.replace("\n", "")
        formatted_lines.append(line)

    return formatted_lines

# Given the output from running fairseq on the test data, get just the actual output
def format_fairseq_output(output):
    formatted_output = []
    # First, just grab all the H-X lines
    for line in output:
        if line.startswith("H-"):
            # The actual word comes after two tabs
            word = line.split("\t")[2]
            formatted_output.append(word)

    return formatted_output

# Gets the boundary-level precision, recall, and F1.
# Prints them all, or a message letting you know if there was an issue with the calculations.
# Returns the three values in a list
def _evaluate_f1(predicted_output, gold_output):
    is_type_sensitive = False
    true_pos = 0
    false_pos = 0
    false_neg = 0

    # Go word by word,
    # then character by character.
    # Because of normalization, the gold and pred words may not have the same number of letters.
    # And obviously, they may not match in where they've put boundaries.
    # We want to look for boundaries between each pair of letters.
    # Rather than just proceeding with a single index which compares the character at pos x in both
    # the predicted and gold output, we will have a count for each word which means we can skip boundaries
    # even when they do not match in the predicted vs. gold.
    # For example, consider:
    # gold: *kʷukʷ-s-cút-s*
    # predicted: *kʷukʷs-cút-s*
    # Starting with kʷ being at index 0 in both words, we first come to a discrepancy at index 3,
    # where the gold has a boundary and the predicted has a letter.
    # This boundary should be counted as usual (i.e., a gold boundary that the prediction missed).
    # However, we will next move *only* the gold count forward, so that the next comparison
    # is at index 4 in the gold (s) but index 3 in the predicted (s).
    # Therefore, the second boundary is fairly evaluated as being correct.
    for pred_seg_word, gold_seg_word in zip(predicted_output, gold_output):
        pred_seg_word = pred_seg_word.replace(" ", "") # Go from w o r d -> word
        gold_seg_word = gold_seg_word.replace(" ", "")

        # We should index fully through each word, because when one ends, the other may have remaining boundaries
        # that must be included in our counts (hence the 'or' below).
        gold_word_index = 0
        pred_word_index = 0
        while gold_word_index < len(gold_seg_word) or pred_word_index < len(pred_seg_word):
            gold_char = gold_seg_word[gold_word_index] if (gold_word_index < len(gold_seg_word)) else None
            pred_char = pred_seg_word[pred_word_index] if (pred_word_index < len(pred_seg_word)) else None
            # Either a true positive or a false negative
            if gold_char in ALL_BOUNDARIES:
                # True positive
                # Depending on value of bool, will check for either an exact boundary match *or* any boundary
                if (is_type_sensitive and gold_char == pred_char) or (not(is_type_sensitive) and pred_char in ALL_BOUNDARIES):
                    true_pos += 1
                    # Increment both counts
                    gold_word_index += 1
                    pred_word_index += 1
                # False Negative
                else:
                    false_neg += 1
                    # Increment only over the boundary
                    gold_word_index += 1
            # False positive
            elif pred_char in ALL_BOUNDARIES:
                false_pos += 1
                # Increment only over the boundary
                pred_word_index += 1
            else:
                # Neither was a boundary, so just increment both counts
                gold_word_index += 1
                pred_word_index += 1

    # Calculations
    # No predicted boundaries -> no precision
    # No gold boundaries -> no recall
    # No predicted OR gold boundaries -> no F1

    # Precision
    if true_pos or false_pos:
        precision_raw = true_pos / (true_pos + false_pos)
        precision = as_percent(precision_raw)
        print(f"\nBoundary-level precision: {(precision)}%.")
    else:
        precision = NO_RESULT_MARKER
        print("\nNo boundary-level precision value due to no predicted boundaries.")

    # Recall
    if true_pos or false_neg:
        recall_raw = true_pos / (true_pos + false_neg)
        recall = as_percent(recall_raw)
        print(f"B-L recall: {(recall)}%.")
    else:
        recall = NO_RESULT_MARKER
        print("\nNo boundary-level recall value due to no gold boundaries.")

    # F1
    if true_pos or false_pos or false_neg:
        f1 = as_percent((2 * true_pos) / ((2 * true_pos) + false_pos + false_neg))
        print(f"B-L F1 Score: {(f1)}%.")
    else:
        f1 = NO_RESULT_MARKER
        f1_alt = NO_RESULT_MARKER
        print("\nNo boundary-level F1 value due to no gold boundaries OR predicted boundaries!")
    # F1 check
    if precision and recall:
        f1_alt = as_percent(2 *((precision_raw * recall_raw) / (precision_raw + recall_raw)))
        assert f1 == f1_alt, f"{f1}, {f1_alt}"

    results = ([precision, recall, f1])
    return results

# No return value, just prints
# Go word-by-word -- the entire thing must be right to be correct!
def _evaluate_word_level_acc(output, gold_output):
    num_words = 0
    num_incorrect_words = 0

    for output_seg_word, gold_seg_word in zip(output, gold_output):
        if output_seg_word != gold_seg_word:
            num_incorrect_words += 1
        num_words += 1

    assert(num_words > 0)
    accuracy = (num_words - num_incorrect_words) / num_words
    accuracy = as_percent(accuracy)
    print(f"\nWord-level accuracy: {accuracy}% on {num_words} words.")
    return accuracy

def evaluate(output, gold_output):
    results = []
    assert len(output) == len(gold_output), f"\nError: There are {len(output)} predicted words, and {len(gold_output)} gold words."
    print("\n** Segmentation accuracy: **")
    results.append(_evaluate_word_level_acc(output, gold_output))
    results.extend(_evaluate_f1(output, gold_output))

    return results

# It may be interesting to know whether the model is under- or over-segmenting
# i.e. inserting too few or too many boundaries
# So let's compare the number of boundaries predicted to the number in the gold version
def compare_boundary_count(output, gold_output):
    predicted_count = _get_boundary_count(output)
    gold_count = _get_boundary_count(gold_output)
    predicted_portion  = (NO_RESULT_MARKER if gold_count <= 0 else as_percent(predicted_count/gold_count))
    if gold_count:
        print(f"\nBoundary count: {predicted_count} predicted vs. {gold_count} in gold ({predicted_portion}%).")
    else:
        print(f"\nBoundary count: {predicted_count} predicted vs. {gold_count} in gold.")

    return predicted_portion

def _get_boundary_count(output):
    boundary_count = 0
    for word in output:
        for boundary in ALL_BOUNDARIES:
            boundary_count += word.count(boundary)

    return boundary_count

# Compare the train and test word-lists to see how many OOV tokens we dealt with
# (Assuming they're OOV if their output differs (rather than their input))
# Plus track performance on just those OOV tokens
# Note that some of these OOV tokens may be repeats
def evaluate_OOV_performance(output, gold_output, train_output):
    OOV_count = 0
    OOV_incorrect_count = 0
    for output_word, gold_word in zip(output, gold_output):
        # If this word is OOV
        if not (gold_word in train_output):
            OOV_count += 1
            if gold_word != output_word:
                OOV_incorrect_count += 1

    OOV_proportion = as_percent(OOV_count / len(output))
    print(f"\nOOV count: {OOV_count}/{len(output)} words ({OOV_proportion}%).")

    OOV_acc = as_percent((OOV_count - OOV_incorrect_count) / OOV_count)
    print(f"OOV accuracy: {OOV_acc}% on {OOV_count} OOV words.\n")

    return [OOV_proportion, OOV_acc]

# Input: a list of predicted segmented words, with no sentence structure
# Look back at the input to figure out where sentence boundaries should be
# Output: a list of predicted segmentation lines (as lists of words)
def reassemble_predicted_line(transcription_lines, predicted_seg_word_list):
    predicted_seg_line_list = []
    current_word_index = 0
    # Go through each input sentence and count the number of words.
    # Then grab that many words from our long list of predicted words, and that will be our prediction line.
    for transcription_line in transcription_lines:
        predicted_seg_line = []
        line_word_count = len(transcription_line.split()) - transcription_line.count(OUT_OF_LANGUAGE_MARKER)
        # Grab the predicted words
        predicted_seg_line.extend(predicted_seg_word_list[current_word_index : current_word_index + line_word_count])
        # Get rid of s p a c e s between letters
        predicted_seg_line = [word.replace(" ", "") for word in predicted_seg_line]
        # Check if we need to add a lang label (for pipeline input)
        if re.search(LANG_LABEL_REGEX, transcription_line):
            lang_label = (re.search(LANG_LABEL_REGEX, transcription_line)).group()
            predicted_seg_line = [word + lang_label for word in predicted_seg_line]

        # Update our progress through the predicted word list
        current_word_index += line_word_count
        predicted_seg_line_list.append(predicted_seg_line)

    return predicted_seg_line_list

def print_predictions(predictions, entire_input):
    formatted_predictions = reassemble_predicted_line((sentence[0] for sentence in entire_input), predictions)
    formatted_predictions = add_back_OOL_words((sentence[0] for sentence in entire_input), formatted_predictions)
    sentences_with_predictions = make_sentence_list_with_prediction(entire_input, formatted_predictions, 1)
    create_file_of_sentences(sentences_with_predictions, PRED_OUTPUT_FILE_NAME, OUTPUT_DIR)

@click.command()
@click.option("--whole_input_file", required=True, help="The name of the input file (i.e., with the transcription, seg, gloss, etc.).")
@click.option("--output_file", required=True, help="The name of the output file.")
# If this not specified, then we assume the output is just a list of words, like the input
@click.option("--output_file_is_fairseq_formatted", is_flag = True, help = "A flag the output has fairseq formatting and needs to be handled as such.")
@click.option("--gold_output_file", required=True, help="The name of the gold output file.")
@click.option("--train_output_file", help="The name of the training output file.")
def main(whole_input_file, output_file, output_file_is_fairseq_formatted, gold_output_file, train_output_file = None):
    print("Comparing these files:", output_file, gold_output_file)
    
    # Get the test results
    output = read_lines_from_file(output_file)
    if output_file_is_fairseq_formatted:
        output = format_fairseq_output(output)

    # Get the labels
    gold_output = read_lines_from_file(gold_output_file)
    
    # Compare!
    results = []
    results.extend(evaluate(output, gold_output))
    results.append(compare_boundary_count(output, gold_output))
    if train_output_file:
        train_output = read_lines_from_file(train_output_file)
        results.extend(evaluate_OOV_performance(output, gold_output, train_output))
    if DO_PRINT_RESULTS_CSV:
        print_results_csv(results, OUTPUT_CSV_HEADER, OUTPUT_CSV, NO_RESULT_MARKER)

    # Print viewable outputs
    # First read in and print out the gold
    # (note this is not just the input to the segmenter, but the ENTIRE input file (4-lines))
    entire_input = read_file(whole_input_file)
    create_file_of_sentences(entire_input, GOLD_OUTPUT_FILE_NAME, OUTPUT_DIR)
    # Now format and print a version with our predictions
    print_predictions(output, entire_input)

# Doing this so that I can export functions to pipeline.py
if __name__ == '__main__':
    main()
