import click
import re
from gloss import make_sentence_list_with_prediction, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY
from glossed_data_utilities import add_back_OOL_words, read_file, write_sentences, OUT_OF_LANGUAGE_MARKER

GOLD_OUTPUT_FILE_NAME = "generated_data/seg_gold.txt"
PRED_OUTPUT_FILE_NAME = "generated_data/seg_pred.txt"
ALL_BOUNDARIES = [LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY]

def _as_percent(number):
    return round(number * 100, 2)

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

# No return value, just prints
def _evaluate_f1(output, gold_output):
    true_pos = 0
    false_pos = 0
    false_neg = 0

    for output_seg_word, gold_seg_word in zip(output, gold_output):
        # Is a true positive a boundary that is in exactly the right position? Recalling that there may be normalization processes.
        # Or should we look at the sequence of boundaries inserted, and check that they're in the right order?
        # Trying the former approach, but it will call a lot of almost-correct boundaries false positives...
        for char_index, char in enumerate(output_seg_word):
            if char in ALL_BOUNDARIES:
                if char_index < len(gold_seg_word) and gold_seg_word[char_index] == char:
                    true_pos += 1
                else:
                    false_pos += 1
            elif char_index < len(gold_seg_word) and gold_seg_word[char_index] in ALL_BOUNDARIES:
                false_neg += 1

    # Calculations
    if true_pos == 0: # Avoid division by 0
        precision = 0
        recall = 0
        f1 = 0
        f1_alt = 0
    else:
        precision = true_pos / (true_pos + false_pos)
        recall = true_pos / (true_pos + false_neg)
        f1 = (2 * true_pos) / ((2 * true_pos) + false_pos + false_neg)
        f1_alt = 2 *((precision * recall) / (precision + recall))

    # Format and print results
    assert(_as_percent(f1) == _as_percent(f1_alt))
    print(f"\nBoundary-level precision: {_as_percent(precision)}%.")
    print(f"B-L recall: {_as_percent(recall)}%.")
    print(f"B-L F1 Score: {_as_percent(f1)}%.")

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
    accuracy = _as_percent(accuracy)
    print(f"\nWord-level accuracy: {accuracy}% on {num_words} words.")

def evaluate(output, gold_output):
    assert len(output) == len(gold_output), f"\nError: There are {len(output)} predicted words, and {len(gold_output)} gold words."
    print("\n** Segmentation accuracy: **")
    _evaluate_word_level_acc(output, gold_output)
    _evaluate_f1(output, gold_output)

# It may be interesting to know whether the model is under- or over-segmenting
# i.e. inserting too few or too many boundaries
# So let's compare the number of boundaries predicted to the number in the gold version
def compare_boundary_count(output, gold_output):
    predicted_count = _get_boundary_count(output)
    gold_count = _get_boundary_count(gold_output)
    if gold_count > 0: # Prevent division by 0
        print(f"\nBoundary count: {predicted_count} predicted vs. {gold_count} in gold ({_as_percent(predicted_count/gold_count)}%).")
    else:
        print(f"\nError generating boundary count: 0 boundaries in gold data!")

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

    print(f"\nOOV count: {OOV_count}/{len(output)} words ({round(OOV_count / len(output) * 100, 2)}%).")

    OOV_acc = (OOV_count - OOV_incorrect_count) / OOV_count
    print(f"OOV accuracy: {_as_percent(OOV_acc)}% on {OOV_count} OOV words.\n")

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

        # Update our progress through the predicted word list
        current_word_index += line_word_count
        predicted_seg_line_list.append(predicted_seg_line)

    return predicted_seg_line_list

def print_predictions(predictions, entire_input):
    formatted_predictions = reassemble_predicted_line((sentence[0] for sentence in entire_input), predictions)
    formatted_predictions = add_back_OOL_words((sentence[0] for sentence in entire_input), formatted_predictions)
    sentences_with_predictions = make_sentence_list_with_prediction(entire_input, formatted_predictions, 1)
    write_sentences(sentences_with_predictions, PRED_OUTPUT_FILE_NAME)

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
    evaluate(output, gold_output)
    compare_boundary_count(output, gold_output)
    if train_output_file:
        train_output = read_lines_from_file(train_output_file)
        evaluate_OOV_performance(output, gold_output, train_output)

    # Print viewable outputs
    # First read in and print out the gold
    # (note this is not just the input to the segmenter, but the ENTIRE input file (4-lines))
    entire_input = read_file(whole_input_file)
    write_sentences(entire_input, GOLD_OUTPUT_FILE_NAME)
    # Now format and print a version with our predictions
    print_predictions(output, entire_input)

# Doing this so that I can export functions to pipeline.py
if __name__ == '__main__':
    main()
