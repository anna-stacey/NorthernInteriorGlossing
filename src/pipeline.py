import click
import re
from test_seg import read_file, format_fairseq_output
from gloss import evaluate_system, extract_X_and_y, format_X_and_y, make_sentence_list_with_prediction, read_datasets, reassemble_gloss_line, train_system, write_output_file, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, REDUPLICATION_BOUNDARY

GOLD_OUTPUT_FILE_NAME = "pipeline_gold.txt"
PRED_OUTPUT_FILE_NAME = "pipeline_pred.txt"

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

def remove_infix_boundary_errors(word_list):
    for i, word in enumerate(word_list):
        if word.count(LEFT_INFIX_BOUNDARY) != word.count(RIGHT_INFIX_BOUNDARY):
            word_list[i] = re.sub(LEFT_INFIX_BOUNDARY, REGULAR_BOUNDARY, word_list[i])
            word_list[i] = re.sub(RIGHT_INFIX_BOUNDARY, REGULAR_BOUNDARY, word_list[i])
        if word.count(LEFT_REDUP_INFIX_BOUNDARY) != word.count(RIGHT_REDUP_INFIX_BOUNDARY):
            word_list[i] = re.sub(LEFT_REDUP_INFIX_BOUNDARY, REDUPLICATION_BOUNDARY, word_list[i])
            word_list[i] = re.sub(RIGHT_REDUP_INFIX_BOUNDARY, REDUPLICATION_BOUNDARY, word_list[i])
    return word_list

@click.command()
@click.option("--seg_output_file", help = "The name of the output file from the segmentation.")
@click.option("--data_summary_file", help = "A text file summary containing the word count in each sentence, created when we preprocess for segmentation.")
@click.option("--gloss_train_file", help = "The name of the file containing all sentences in the train set.")
@click.option("--gloss_dev_file", help = "The name of the file containing all sentences in the dev set.")
@click.option("--gloss_test_file", help = "The name of the file containing all sentences in the test set.")
@click.option("--segmentation_line_number", help = "The line that contains the segmented sentence.  For example if there are four lines each and the segmentation is the second line, this will be 2.")
@click.option("--gloss_line_number", help = "The line that contains the glossed sentence.  For example if there are four lines each and the gloss is the third line, this will be 3.")
def main(seg_output_file, data_summary_file, gloss_train_file, gloss_dev_file, gloss_test_file, segmentation_line_number, gloss_line_number):
    # Convert right away to prevent off-by-one errors
    gloss_line_number = int(gloss_line_number) - 1
    segmentation_line_number = int(segmentation_line_number) - 1

    # Read in our word counts, for re-assembling sentences
    word_count_by_sentence = read_file(data_summary_file)
    # Read in the fairseq output (segmented words)
    seg_output = read_file(seg_output_file)
    # Process the gross fairseq output format so we just have the words
    seg_output = format_fairseq_output(seg_output)
    # Remove spaces from words
    seg_output = [word.replace(" ", "") for word in seg_output]
    # For now... remove single infix markers (incorrect!)
    seg_output = remove_infix_boundary_errors(seg_output)
    # Put the sentences back together
    test_X = reassemble_sentences(seg_output, word_count_by_sentence)
    # Ok! Now we have our input prepped. Now let's get our gold standard glosses
    train, throwaway, test = read_datasets(gloss_train_file, gloss_dev_file, gloss_test_file)
    throwaway, test_y = extract_X_and_y(test, segmentation_line_number, gloss_line_number)

    # Keep versions with boundaries for word-by-word evaluation
    test_X_with_boundaries = test_X
    test_y_with_boundaries = test_y

    # Create the model
    train_X, train_y = extract_X_and_y(train, segmentation_line_number, gloss_line_number)
    train_X, train_y = format_X_and_y(train_X, train_y)
    throwaway, stem_dict, crf = train_system(train_X, train_y)

    # Now we can format the input and output for glossing
    test_X, test_y = format_X_and_y(test_X, test_y)
    # print(len(test_X), len(test_y))
    pred_y = evaluate_system(test_X, test_y, test_X_with_boundaries, test_y_with_boundaries, crf, stem_dict)

    # Create output files for the sigmorphon evaluation
    isOpenTrack = True # Make this true if you want to see the segmentation output, too
    # Assemble output file of predictions
    test_with_predictions = make_sentence_list_with_prediction(test, reassemble_gloss_line(pred_y), gloss_line_number)
    write_output_file(test_with_predictions, PRED_OUTPUT_FILE_NAME, segmentation_line_number, gloss_line_number, isOpenTrack)
    # And create a file of the gold version, formatted the same way to permit comparison
    write_output_file(test, GOLD_OUTPUT_FILE_NAME, segmentation_line_number, gloss_line_number, isOpenTrack)

main()
