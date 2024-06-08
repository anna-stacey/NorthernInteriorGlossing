import click
from gloss import make_sentence_list_with_prediction, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY
from glossed_data_utilities import add_back_OOL_words, read_file, write_sentences, OUT_OF_LANGUAGE_MARKER

GOLD_OUTPUT_FILE_NAME = "generated_data/seg_gold.txt"
PRED_OUTPUT_FILE_NAME = "generated_data/seg_pred.txt"
ALL_BOUNDARIES = [LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY]

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

# No return value
# Evaluate the accuracy word by word
def evaluate(output, gold_output):
    assert(len(output) == len(gold_output))
    seg_count = 0
    incorrect_seg_count = 0
    for output_seg, gold_seg in zip(output, gold_output):
        if output_seg != gold_seg:
            incorrect_seg_count += 1
        seg_count += 1

    assert(seg_count > 0)
    accuracy = (seg_count - incorrect_seg_count) / seg_count
    accuracy = round(accuracy * 100, 2)
    print(f"\nAccuracy: {accuracy}% on {seg_count} words.")

# It may be interesting to know whether the model is under- or over-segmenting
# i.e. inserting too few or too many boundaries
# So let's compare the number of boundaries predicted to the number in the gold version
def compare_boundary_count(output, gold_output):
    predicted_count = _get_boundary_count(output)
    gold_count = _get_boundary_count(gold_output)
    print(f"Boundary count: {predicted_count} predicted vs. {gold_count} in gold ({round(predicted_count/gold_count * 100, 2)}%).")

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

    OOV_acc = round((OOV_count - OOV_incorrect_count) / OOV_count * 100, 2)
    print(f"OOV accuracy: {OOV_acc}% on {OOV_count} OOV words.\n")

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
@click.option("--whole_input_file", help="The name of the input file (i.e., with the transcription, seg, gloss, etc.).")
@click.option("--output_file", help="The name of the output file.")
# If this not specified, then we assume the output is just a list of words, like the input
@click.option("--output_file_is_fairseq_formatted", is_flag = True, help = "A flag the output has fairseq formatting and needs to be handled as such.")
@click.option("--gold_output_file", help="The name of the gold output file.")
@click.option("--train_output_file", help="The name of the training output file.")
def main(whole_input_file, output_file, output_file_is_fairseq_formatted, gold_output_file, train_output_file):
    print("Comparing these files:", output_file, gold_output_file)
    
    # Get the test results
    output = read_lines_from_file(output_file)
    if output_file_is_fairseq_formatted:
        output = format_fairseq_output(output)

    # Get the labels
    gold_output = read_lines_from_file(gold_output_file)
    train_output = read_lines_from_file(train_output_file)
    
    # Compare!
    evaluate(output, gold_output)
    compare_boundary_count(output, gold_output)
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
