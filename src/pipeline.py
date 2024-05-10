import click
import re
from gloss import evaluate_system, extract_X_and_y, format_X_and_y, make_sentence_list_with_prediction, read_datasets, reassemble_predicted_words, train_system, write_output_file, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, REDUPLICATION_BOUNDARY
from glossed_data_utilities import add_back_OOL_words, handle_OOL_words, read_file
from prescreen_data import DOUBLE_BOUNDARY_REGEX

GOLD_OUTPUT_FILE_NAME = "pipeline_gold.txt"
PRED_OUTPUT_FILE_NAME = "pipeline_pred.txt"
IS_OPEN_TRACK = True # Make this true if you want to see the segmentation output, too

# Convert from a list of words, to a list of sentences
def reassemble_sentences(word_list, word_count_by_sentence):
    sentence_list = []
    current_word_index = 0
    for word_count in word_count_by_sentence:
        current_word_count = int(word_count)
        current_sentence = word_list[current_word_index : current_word_index + current_word_count]
        current_sentence = " ".join(current_sentence)
        current_word_index += current_word_count
        sentence_list.append(current_sentence)

    return sentence_list

# Input: a list of segmentation lines, as strings
def remove_boundary_errors(seg_line_list):
    updated_seg_line_list = []
    for seg_line in seg_line_list:
        word_list = seg_line.split()
        for i, word in enumerate(word_list):
            # Handle infix boundary errors
            if word.count(LEFT_INFIX_BOUNDARY) != word.count(RIGHT_INFIX_BOUNDARY):
                word_list[i] = re.sub(LEFT_INFIX_BOUNDARY, REGULAR_BOUNDARY, word_list[i])
                word_list[i] = re.sub(RIGHT_INFIX_BOUNDARY, REGULAR_BOUNDARY, word_list[i])
            if word.count(LEFT_REDUP_INFIX_BOUNDARY) != word.count(RIGHT_REDUP_INFIX_BOUNDARY):
                word_list[i] = re.sub(LEFT_REDUP_INFIX_BOUNDARY, REDUPLICATION_BOUNDARY, word_list[i])
                word_list[i] = re.sub(RIGHT_REDUP_INFIX_BOUNDARY, REDUPLICATION_BOUNDARY, word_list[i])
            # Fix any instances of double boundaries (e.g. one time the segmentation split abc as ab--c)
            if re.search(DOUBLE_BOUNDARY_REGEX, word):
                word_list[i] = re.sub(DOUBLE_BOUNDARY_REGEX, REGULAR_BOUNDARY, word_list[i])

        updated_seg_line = " ".join(word_list)
        updated_seg_line_list.append(updated_seg_line)

    return updated_seg_line_list

@click.command()
@click.option("--seg_pred_file", help = "The name of the predicted file from the segmentation process.")
@click.option("--gloss_train_file", help = "The name of the file containing all sentences in the train set.")
@click.option("--gloss_dev_file", help = "The name of the file containing all sentences in the dev set.")
@click.option("--gloss_test_file", help = "The name of the file containing all sentences in the test set.")
@click.option("--segmentation_line_number", help = "The line that contains the segmented sentence.  For example if there are four lines each and the segmentation is the second line, this will be 2.")
@click.option("--gloss_line_number", help = "The line that contains the glossed sentence.  For example if there are four lines each and the gloss is the third line, this will be 3.")
def main(seg_pred_file, gloss_train_file, gloss_dev_file, gloss_test_file, segmentation_line_number, gloss_line_number):
    # Convert right away to prevent off-by-one errors
    gloss_line_number = int(gloss_line_number) - 1
    segmentation_line_number = int(segmentation_line_number) - 1

    # First, let's read in the original train and test sets
    train, throwaway, test = read_datasets(gloss_train_file, gloss_dev_file, gloss_test_file)
    # Before preparing the test set for glossing, we can first use it to make the gold output file
    write_output_file(test, GOLD_OUTPUT_FILE_NAME, segmentation_line_number, gloss_line_number, IS_OPEN_TRACK)

    # Next, get the predicted seg lines.  These will be our input.
    seg_output = read_file(seg_pred_file)
    seg_line_predictions = (sentence[1] for sentence in seg_output)
    # For now... remove single infix markers (incorrect!)
    seg_line_predictions = remove_boundary_errors(seg_line_predictions)
    # Modify our test set to contain the *predicted* seg lines
    test = make_sentence_list_with_prediction(test, seg_line_predictions, 1)
    # Now we have the original training set,
    # and a test set with the correct X and y for the pipeline.

    # Replace them with "OOL" for now, but after feature generation the formatting code will remove these tokens altogether
    train, test = handle_OOL_words([train, test], replace = True)[:2]

    test_X, test_y = extract_X_and_y(test, segmentation_line_number, gloss_line_number)

    # Keep versions with boundaries (but no OOL tokens!) for word-by-word evaluation
    test_without_OOL = handle_OOL_words([test])[0]
    test_X_with_boundaries, test_y_with_boundaries  = extract_X_and_y(test_without_OOL, segmentation_line_number, gloss_line_number)

    # Create the model
    train_X, train_y = extract_X_and_y(train, segmentation_line_number, gloss_line_number)
    train_X, train_y = format_X_and_y(train_X, train_y)
    throwaway, stem_dict, crf = train_system(train_X, train_y)

    # Now we can format the input and output for glossing
    test_X, test_y = format_X_and_y(test_X, test_y)
    pred_y = evaluate_system(test_X, test_y, test_X_with_boundaries, test_y_with_boundaries, crf, stem_dict)

    # Create the predictions output file
    # Add back OOl words to our predicted gloss lines (using untouched transcription lines)
    pred_y_to_print = add_back_OOL_words(list(sentence[0] for sentence in seg_output), reassemble_predicted_words(pred_y))
    # Now we can just take the printed output from the seg step, and add in our new gloss line predictions
    test_with_predictions = make_sentence_list_with_prediction(seg_output, pred_y_to_print, gloss_line_number)
    # Write!
    write_output_file(test_with_predictions, PRED_OUTPUT_FILE_NAME, segmentation_line_number, gloss_line_number, IS_OPEN_TRACK)


main()
