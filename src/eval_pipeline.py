import click
from eval_gloss import evaluate_system
from gloss import add_word_boundaries_to_gloss, deal_with_stems, extract_X_and_y, sentence_to_features, sentence_to_glosses, reassemble_predicted_words
from glossed_data_utilities import handle_OOL_words, print_results_csv, read_file
from test_seg import evaluate
from preprocess_seg import sentence_list_to_word_list

OUTPUT_CSV = "./pipeline_results.csv"
OUTPUT_CSV_HEADER = "Morpheme Acc,Word Acc,Stem Acc,Gram Acc"
NO_RESULTS_MARKER = None

@click.command()
@click.option("--test_file", help = "The name of the file containing all sentences in the test set.")
@click.option("--output_file", help = "The name of the file containing all predicted output (i.e., the test set, but with the gloss line replaced with our system's output).")
@click.option("--segmentation_line_number", help = "The line that contains the segmented sentence.  For example if there are four lines each and the segmentation is the second line, this will be 2.")
@click.option("--gloss_line_number", help = "The line that contains the glossed sentence.  For example if there are four lines each and the gloss is the third line, this will be 3.")
def main(test_file, output_file, segmentation_line_number, gloss_line_number):
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
    test_y = [sentence_to_glosses(gloss_line, keep_word_boundaries = True) for gloss_line in test_y]
    pred_y = [sentence_to_glosses(gloss_line, keep_word_boundaries = True) for gloss_line in pred_y]

    # Evaluate system
    # For stem/gram eval, we need a version of the predictions where all the stems are identified (in this case, by being glossed as just "STEM")
    pred_y_no_stems = [deal_with_stems((sentence_to_features(example[segmentation_line_number])), (sentence_to_glosses(example[gloss_line_number])))[0] for example in predictions]
    # Calling deal_with_stems returns a pred_y without word boundaries, so add them back now to keep our results in a consistent format
    pred_y_no_stems = add_word_boundaries_to_gloss(pred_y_no_stems, pred_X)
    results = evaluate_system(test_y, pred_y, pred_y_no_stems)

    # Run the word-by-word eval from the segmentation stage (unlike the glossing one, it checks boundary type)
    # We need the gold and predicted gloss lines each as one list of words
    test_y_word_list = sentence_list_to_word_list([line.split() for line in test_y_sentences])
    pred_y_reassembled = reassemble_predicted_words([line.split() for line in pred_X], pred_y)
    pred_y_word_list = sentence_list_to_word_list(pred_y_reassembled)
    evaluate(pred_y_word_list, test_y_word_list)

    print_results_csv(results, OUTPUT_CSV_HEADER, OUTPUT_CSV, NO_RESULTS_MARKER)

if __name__ == '__main__':
    main()
