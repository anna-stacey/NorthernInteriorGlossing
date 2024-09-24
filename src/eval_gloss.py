import click
from gloss import add_word_boundaries_to_gloss, deal_with_stems, extract_X_and_y, sentence_to_features, sentence_to_glosses
from glossed_data_utilities import as_percent, handle_OOL_words, print_results_csv, read_file

OUTPUT_CSV = "./gloss_results.csv"
OUTPUT_CSV_HEADER = "Morpheme Acc,Word Acc,Stem Acc,Gram Acc"
NO_RESULTS_MARKER = None

# Returns scores (as percents)
def evaluate_system(y, pred_y, interim_pred_y):
    # Evaluate the overall result
    morpheme_acc = as_percent(get_morpheme_level_accuracy(y, pred_y))
    word_acc = as_percent(get_word_level_accuracy(y, pred_y))
    print("\n** Glossing accuracy: **")
    print(f"Morpheme-level accuracy: {morpheme_acc}%.\n")
    print(f"Word-level accuracy: {word_acc}%.\n")

    # Results - print by-stem and by-gram accuracy
    stem_acc, gram_acc = get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y)

    return [morpheme_acc, word_acc, stem_acc, gram_acc]

# Returns the accuracy value - this version includes going word-by-word
# Expects a list of sentences as lists of words as lists of morphemes
def get_morpheme_level_accuracy(y, predicted_y):
    assert(len(y) == len(predicted_y))
    total = 0
    wrong = 0

    for gold_label_line, predicted_label_line in zip(y, predicted_y):
        # There must be the same number of words in the gold and the predicted lines
        # (The number of words is not impacted by the segmentation task)
        assert(len(gold_label_line) == len(predicted_label_line))
        wrong_per_sentence = 0
        for gold_word, predicted_word in zip(gold_label_line, predicted_label_line):
            # The number of morphemes can vary in the gold word vs the predicted word
            # So this zip may end up skipping some morphemes if one word contains more
            for gold_label, predicted_label in zip(gold_word, predicted_word):
                total += 1
                if gold_label != predicted_label:
                    wrong += 1
                    wrong_per_sentence +=1

    assert(total > 0)
    accuracy = (total - wrong) / total
    return accuracy

# Returns the accuracy value
# Expects a list of sentences as lists of words as lists of morphemes
# Operates at the word-level, i.e., a word must have all its morphemes
# glossed correctly to be considered correct
def get_word_level_accuracy(y, predicted_y):
    assert(len(y) == len(predicted_y))
    total = 0
    wrong = 0

    for gold_label_line, predicted_label_line in zip(y, predicted_y):
        # There must be the same number of words in the gold and the predicted lines
        # (The number of words is not impacted by the segmentation task)
        assert(len(gold_label_line) == len(predicted_label_line))

        for gold_word, predicted_word in zip(gold_label_line, predicted_label_line):
            total += 1
            is_correct = True
            # The number of morphemes can vary in the gold word vs the predicted word
            # So this zip may end up skipping some morphemes if one word contains more
            for gold_label, predicted_label in zip(gold_word, predicted_word):
                if gold_label != predicted_label:
                    is_correct = False

            # Was any morpheme in the word wrong?  If so, mark the whole word wrong.
            if not is_correct:
                wrong += 1

    assert(total > 0)
    accuracy = (total - wrong) / total
    return accuracy

# Returns the two accuracy values (as percents)
def get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y):
    # Divide up the predictions and gold labels into stems and grams
    # We know which are stems at this point - they're labelled stem in the interim set
    pred_y_stems = []
    pred_y_grams = []
    y_stems = []
    y_grams = []
    # We need to build up the lists sentence-by-sentence, bc of the way evaluation works
    pred_y_stems_sentence = []
    pred_y_grams_sentence = []
    y_stems_sentence = []
    y_grams_sentence = []
    # Go sentence by sentence
    for sentence_without_stems, sentence_with_stems, gold_sentence in zip(interim_pred_y, pred_y, y):
        # Word by word
        for word_without_stems, word_with_stems, gold_word in zip(sentence_without_stems, sentence_with_stems, gold_sentence):
            # Morpheme by morpheme
            for gloss_without_stems, gloss_with_stems, gold_gloss in zip(word_without_stems, word_with_stems, gold_word):
                if gloss_without_stems == 'STEM': # It's a stem
                    pred_y_stems_sentence.append(gloss_with_stems)
                    y_stems_sentence.append(gold_gloss)
                else: # It's a gram
                    pred_y_grams_sentence.append(gloss_without_stems)
                    y_grams_sentence.append(gold_gloss)
    
        # End of sentence reached; add it to our lists and reset
        pred_y_stems.append(pred_y_stems_sentence)
        pred_y_grams.append(pred_y_grams_sentence)
        y_stems.append(y_stems_sentence)
        y_grams.append(y_grams_sentence)
        pred_y_stems_sentence = []
        pred_y_grams_sentence = []
        y_stems_sentence = []
        y_grams_sentence = []

    # Now each list has one entry per sentence, which is itself a list of morphemes
    stem_acc = as_percent(get_simple_morpheme_level_accuracy(y_stems, pred_y_stems))
    gram_acc = as_percent(get_simple_morpheme_level_accuracy(y_grams, pred_y_grams))
    print(f"Accuracy for stems: {stem_acc}%.")
    print(f"Accuracy for grams: {gram_acc}%.")

    return stem_acc, gram_acc

# Returns the accuracy value (for each morpheme)
# Expects a list of sentences as lists of morphemes
def get_simple_morpheme_level_accuracy(y, predicted_y):
    assert len(y) == len(predicted_y), f"Mismatch between length of gold glosses ({len(y)}) and length of predicted glosses ({len(predicted_y)})."
    total = 0
    wrong = 0
    for gold_label_line, predicted_label_line in zip(y, predicted_y):
        for gold_label, predicted_label in zip(gold_label_line, predicted_label_line):
            total += 1
            if gold_label != predicted_label:
                wrong += 1
    
    assert(total > 0)
    accuracy = (total - wrong) / total
    return accuracy

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
    test_X, pred_y = extract_X_and_y(predictions, segmentation_line_number, gloss_line_number)
    # Get the sentence as a list of words, where each word is a list of morphemes
    test_y = [sentence_to_glosses(gloss_line, keep_word_boundaries = True) for gloss_line in test_y]
    pred_y = [sentence_to_glosses(gloss_line, keep_word_boundaries = True) for gloss_line in pred_y]

    # Evaluate system
    # For stem/gram eval, we need a version of the predictions where all the stems are identified (in this case, by being glossed as just "STEM")
    pred_y_no_stems = [deal_with_stems((sentence_to_features(example[segmentation_line_number])), (sentence_to_glosses(example[gloss_line_number])))[0] for example in predictions]
    # Calling deal_with_stems returns a pred_y without word boundaries, so add them back now to keep our results in a consistent format
    pred_y_no_stems = add_word_boundaries_to_gloss(pred_y_no_stems, test_X)
    results = evaluate_system(test_y, pred_y, pred_y_no_stems)

    print_results_csv(results, OUTPUT_CSV_HEADER, OUTPUT_CSV, NO_RESULTS_MARKER)

if __name__ == '__main__':
    main()