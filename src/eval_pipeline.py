import click
from copy import deepcopy
from eval_gloss import evaluate_system
from gloss import add_word_boundaries_to_gloss, deal_with_stems, extract_X_and_y, seg_line_to_features, gloss_line_to_morphemes, reassemble_predicted_words
from glossed_data_utilities import as_percent, handle_OOL_words, print_results_csv, read_file
from test_seg import evaluate, evaluate_OOV_performance, read_lines_from_file
from preprocess_seg import sentence_list_to_word_list

OUTPUT_CSV = "./pipeline_results.csv"
OUTPUT_CSV_HEADER = "Morpheme Acc,Bag o' Words,Word Acc (incl. boundaries),OOV Count,OOV Acc"
NO_RESULTS_MARKER = None

# Expects a list of sentences as lists of words as lists of morphemes
def bag_of_words(y, pred_y):
    pred_y_copy = deepcopy(pred_y) # Prevent modifying the argument
    assert(len(y) == len(pred_y))
    total_morphemes = 0
    wrong_morphemes = 0

    for gold_label_line, predicted_label_line in zip(y, pred_y_copy):
        # There must be the same number of words in the gold and the predicted lines
        # (The number of words is not impacted by the segmentation task)
        assert len(gold_label_line) == len(predicted_label_line), f"Length mismatch! The gold line has {len(gold_label_line)} words, while the predicted line has {len(predicted_label_line)} words.\nGold line: {gold_label_line}\nPredicted line: {predicted_label_line}"
        for gold_word, predicted_word in zip(gold_label_line, predicted_label_line):
            # The number of morphemes can vary in the gold word vs the predicted word
            # So this check simply checks every *gold* morpheme
            for i, gold_label in enumerate(gold_word):
                total_morphemes += 1
                if not (gold_label in predicted_word):
                    wrong_morphemes += 1
                else:
                    predicted_word.remove(gold_label) # Prevent duplicate matches

    accuracy = as_percent((total_morphemes - wrong_morphemes) / total_morphemes) if total_morphemes > 0 else NO_RESULTS_MARKER
    print(f"Bag o' words morpheme-level accuracy: {accuracy}%.\n" if not(accuracy == NO_RESULTS_MARKER) else "No bag o' words morpheme-level accuracy because there are no morphemes!")
    return accuracy

@click.command()
@click.option("--test_file", required = True, help = "The name of the file containing all sentences in the test set.")
@click.option("--output_file", required = True, help = "The name of the file containing all predicted output (i.e., the test set, but with the gloss line replaced with our system's output).")
@click.option("--segmentation_line_number", required = True, help = "The line that contains the segmented sentence.  For example if there are four lines each and the segmentation is the second line, this will be 2.")
@click.option("--gloss_line_number", required = True, help = "The line that contains the glossed sentence.  For example if there are four lines each and the gloss is the third line, this will be 3.")
@click.option("--train_input_file", help="The name of the training input file, for optional OOV calculations.")
@click.option("--test_input_file", help="The name of the test input file, for optional OOV calculations.")
def main(test_file, output_file, segmentation_line_number, gloss_line_number, train_input_file = None, test_input_file = None):
    # Convert right away to prevent off-by-one errors
    segmentation_line_number = int(segmentation_line_number) - 1
    gloss_line_number = int(gloss_line_number) - 1

    # Read in the gold and predicted files
    test = read_file(test_file)
    predictions = read_file(output_file)
    # Remove OOL words (not used in evaluation!)
    [test, predictions] = handle_OOL_words([test, predictions])
    # Separate the gloss line (y)
    test_X, test_y = extract_X_and_y(test, segmentation_line_number, gloss_line_number)
    pred_X, pred_y = extract_X_and_y(predictions, segmentation_line_number, gloss_line_number)
    test_y_sentences = test_y
    # Get the sentence as a list of words, where each word is a list of morphemes
    test_y = [gloss_line_to_morphemes(gloss_line, keep_word_boundaries = True) for gloss_line in test_y]
    pred_y = [gloss_line_to_morphemes(gloss_line, keep_word_boundaries = True) for gloss_line in pred_y]

    # Evaluate system
    # For stem/gram eval, we need a version of the predictions where all the stems are identified (in this case, by being glossed as just "STEM")
    pred_y_no_stems = [deal_with_stems((seg_line_to_features(example[segmentation_line_number])), (gloss_line_to_morphemes(example[gloss_line_number])))[0] for example in predictions]
    # Calling deal_with_stems returns a pred_y without word boundaries, so add them back now to keep our results in a consistent format
    pred_y_no_stems = add_word_boundaries_to_gloss(pred_y_no_stems, pred_X)
    results = [(evaluate_system(test_y, pred_y, pred_y_no_stems))[0]] # Ditch everything but the morpheme acc (for now...)

    results.append(bag_of_words(test_y, pred_y))

    # Run the word-by-word eval from the segmentation stage (unlike the glossing one, it checks boundary type)
    # We need the gold and predicted gloss lines each as one list of words
    test_y_word_list = sentence_list_to_word_list([line.split() for line in test_y_sentences])
    pred_y_reassembled = reassemble_predicted_words([line.split() for line in pred_X], pred_y)
    pred_y_word_list = sentence_list_to_word_list(pred_y_reassembled)
    results.append(evaluate(pred_y_word_list, test_y_word_list)[0]) # Omit the boundary-focussed results

    if train_input_file and test_input_file:
        train_input = read_lines_from_file(train_input_file)
        test_input = read_lines_from_file(test_input_file)
        results.extend(evaluate_OOV_performance(pred_y_word_list, test_y_word_list, train_input, test_input))

    print_results_csv(results, OUTPUT_CSV_HEADER, OUTPUT_CSV, NO_RESULTS_MARKER)

if __name__ == '__main__':
    main()
