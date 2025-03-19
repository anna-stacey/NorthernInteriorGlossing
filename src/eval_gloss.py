import click
import json
import re
from gloss import add_word_boundaries_to_gloss, deal_with_stems, extract_X_and_y, gloss_line_to_morphemes, match_stem, seg_line_to_features, seg_line_to_morphemes
from glossed_data_utilities import as_percent, handle_OOL_words, print_results_csv, read_file

OUTPUT_CSV = "./gloss_results.csv"
OUTPUT_CSV_HEADER = "Morpheme Acc,Word Acc,Identified Stem Acc,Identified Gram Acc,True Stem Acc,True Gram Acc"
NO_RESULTS_MARKER = None

# Returns scores (as percents)
# include_stem_gram_scores is an option because those metrics should only be
# calculated when the number of morphemes is guaranteed to be correct
# (i.e., for the glossing stage only, not for the pipeline)
# test_X/stem_dict is used to calculate the IV stem accuracy, so can be left out if
# you're not calculating stem-only accuracies (i.e., for the pipeline)
def evaluate_system(y, pred_y, interim_pred_y, include_stem_gram_scores = True, test_X = None, stem_dict = None):
    # Evaluate the overall result
    print("\n** Glossing accuracy: **")
    morpheme_acc = get_morpheme_level_accuracy(y, pred_y)
    print(f"Morpheme-level accuracy: {morpheme_acc}%.\n" if not(morpheme_acc == NO_RESULTS_MARKER) else "No morpheme-level accuracy because there are no morphemes!")
    word_acc = get_word_level_accuracy(y, pred_y)
    print(f"Word-level accuracy: {word_acc}%.\n" if not(word_acc == NO_RESULTS_MARKER) else "No word-level accuracy because there are no words!")
    results = [morpheme_acc, word_acc]

    # Print by-stem and by-gram accuracy
    if include_stem_gram_scores:
        if test_X and stem_dict:
            accs = get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y, test_X)
            gram_acc = accs[0]
            stem_acc = accs[1]
            print(f"Accuracy for morphemes *identified as* stems: {stem_acc}%." if not(stem_acc == NO_RESULTS_MARKER) else "No identified stem accuracy because no morphemes were identified as stems!")
            print(f"Accuracy for morphemes *identified as* grams: {gram_acc}%." if not(gram_acc == NO_RESULTS_MARKER) else "No identified gram accuracy because no morphemes were identified as grams!")
            results.extend([stem_acc, gram_acc])

            accs = get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y, test_X, use_system_categorization = False, stem_dict = stem_dict)
            actual_gram_acc = accs[0]
            actual_stem_acc = accs[1]
            actual_IV_stem_acc = accs[2]
            print(f"Accuracy for morphemes that *really are* stems: {actual_stem_acc}%." if not(actual_stem_acc == NO_RESULTS_MARKER) else "No actual stem accuracy because there are no stems!")
            print(f"Accuracy for morphemes that *really are* stems *and are in-vocabulary*: {actual_IV_stem_acc}%." if not(actual_IV_stem_acc == NO_RESULTS_MARKER) else "No actual stem accuracy (for in-vocab stems) because there are no stems!")
            print(f"Accuracy for morphemes that *really are* grams: {actual_gram_acc}%." if not(actual_gram_acc == NO_RESULTS_MARKER) else "No actual gram accuracy because there are no grams!")
            results.extend([actual_stem_acc, actual_gram_acc])
        else:
            print("\nERROR: Can't calculate stem/gram accuracy -- missing input parameters.")

    return results

# Returns the accuracy value - this version includes going word-by-word
# Expects a list of sentences as lists of words as lists of morphemes
def get_morpheme_level_accuracy(y, predicted_y, structured = True):
    assert(len(y) == len(predicted_y))
    total = 0
    wrong = 0

    if structured:
        for gold_label_line, predicted_label_line in zip(y, predicted_y):
            # There must be the same number of words in the gold and the predicted lines
            # (The number of words is not impacted by the segmentation task)
            assert len(gold_label_line) == len(predicted_label_line), f"Length mismatch! The gold line has {len(gold_label_line)} words, while the predicted line has {len(predicted_label_line)} words.\nGold line: {gold_label_line}\nPredicted line: {predicted_label_line}"
            for gold_word, predicted_word in zip(gold_label_line, predicted_label_line):
                # The number of morphemes can vary in the gold word vs the predicted word
                # So this check simply checks every *gold* morpheme
                for i, gold_label in enumerate(gold_word):
                    total += 1
                    if i >= len(predicted_word) or gold_label != predicted_word[i]:
                        wrong += 1
    else:
        for i, gold_label in enumerate(y):
            total += 1
            if i >= len(predicted_y) or gold_label != predicted_y[i]:
                wrong += 1

    accuracy = as_percent((total - wrong) / total) if total > 0 else NO_RESULTS_MARKER
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
            # So this check simply checks every *gold* morpheme
            for i, gold_label in enumerate(gold_word):
                if i >= len(predicted_word) or gold_label != predicted_word[i]:
                    is_correct = False

            # Was any morpheme in the word wrong?  If so, mark the whole word wrong.
            if not is_correct:
                wrong += 1

    accuracy = as_percent((total - wrong) / total) if total > 0 else NO_RESULTS_MARKER
    return accuracy

# Returns the two accuracy values (as percents)
# Note that this metric is only intended for the glossing stage,
# and is kept simple, not made for the complications of the pipeline stage.
# If use_system_categorization = True:
# Morphemes are categorized into stems/grams based on what the *system* has identified them as.
# (i.e., if the system marks a morpheme as STEM, it's a stem!)
# If use_system_categorization = False:
# Morphemes are categorized into stems/grams based on what they *actually* are in the gold data.
# (i.e., if the gloss is lowercase, it's a stem!)
# test_X (and optional stem_dict) are only used for the *actual* categorization accuracies (spec. for IV stem accuracy)
def get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y, test_X, use_system_categorization = True, stem_dict = None):
    # Divide up the predictions and gold labels into stems and grams
    pred_y_grams = []
    y_grams = []
    pred_y_stems = []
    y_stems = []
    IV_pred_y_stems = []
    IV_y_stems = []

    # Go sentence by sentence
    for input_sentence, sentence_without_stems, sentence_with_stems, gold_sentence in zip(test_X, interim_pred_y, pred_y, y):
        # Word by word
        for input_word, word_without_stems, word_with_stems, gold_word in zip(input_sentence, sentence_without_stems, sentence_with_stems, gold_sentence):
            # Morpheme by morpheme
            # This check is gloss stage only, so the number of morphemes should be the same.
            assert(len(word_with_stems) == len(gold_word))
            assert(len(word_without_stems) == len(word_with_stems))
            for input_gloss, gloss_without_stems, gloss_with_stems, gold_gloss in zip(input_word, word_without_stems, word_with_stems, gold_word):
                if use_system_categorization:
                    if gloss_without_stems == 'STEM': # It's a stem
                        pred_y_stems.append(gloss_with_stems)
                        y_stems.append(gold_gloss)
                    else: # It's a gram
                        pred_y_grams.append(gloss_without_stems)
                        y_grams.append(gold_gloss)
                else:
                    if re.search(r'[a-z]', gold_gloss): # It's a stem
                        pred_y_stems.append(gloss_with_stems)
                        y_stems.append(gold_gloss)
                        if stem_dict and match_stem(input_gloss, stem_dict): # It's an IV stem
                            IV_pred_y_stems.append(gloss_with_stems)
                            IV_y_stems.append(gold_gloss)
                    else: # It's a gram
                        pred_y_grams.append(gloss_without_stems)
                        y_grams.append(gold_gloss)

    # Now each list has one entry per sentence, which is itself a list of morphemes
    stem_acc = get_morpheme_level_accuracy(y_stems, pred_y_stems, structured = False)
    IV_stem_acc = get_morpheme_level_accuracy(IV_y_stems, IV_pred_y_stems, structured = False)
    gram_acc = get_morpheme_level_accuracy(y_grams, pred_y_grams, structured = False)

    return [gram_acc, stem_acc, IV_stem_acc]

@click.command()
@click.option("--test_file", help = "The name of the file containing all sentences in the test set.")
@click.option("--output_file", help = "The name of the file containing all predicted output (i.e., the test set, but with the gloss line replaced with our system's output).")
@click.option("--segmentation_line_number", help = "The line that contains the segmented sentence.  For example if there are four lines each and the segmentation is the second line, this will be 2.")
@click.option("--gloss_line_number", help = "The line that contains the glossed sentence.  For example if there are four lines each and the gloss is the third line, this will be 3.")
def main(test_file, output_file, segmentation_line_number, gloss_line_number):
    # Convert right away to prevent off-by-one errors
    segmentation_line_number = int(segmentation_line_number) - 1
    gloss_line_number = int(gloss_line_number) - 1

    # Read in the stem_dict for IV stem categorization
    with open("./stem_dict.txt", "r") as file:
        stem_dict = json.load(file)
    # Read in the gold and predicted files
    test = read_file(test_file)
    predictions = read_file(output_file)
    # Remove OOL words (not used in evaluation!)
    [test, predictions] = handle_OOL_words([test, predictions])
    # Separate the gloss line (y)
    test_X, test_y = extract_X_and_y(test, segmentation_line_number, gloss_line_number)
    test_X, pred_y = extract_X_and_y(predictions, segmentation_line_number, gloss_line_number)
    # Get the sentence as a list of words, where each word is a list of morphemes
    test_y = [gloss_line_to_morphemes(gloss_line, keep_word_boundaries = True) for gloss_line in test_y]
    pred_y = [gloss_line_to_morphemes(gloss_line, keep_word_boundaries = True) for gloss_line in pred_y]

    # Evaluate system
    # For stem/gram eval, we need a version of the predictions where all the stems are identified (in this case, by being glossed as just "STEM")
    pred_y_no_stems = [deal_with_stems((seg_line_to_features(example[segmentation_line_number])), (gloss_line_to_morphemes(example[gloss_line_number])))[0] for example in predictions]
    # Calling deal_with_stems returns a pred_y without word boundaries, so add them back now to keep our results in a consistent format
    pred_y_no_stems = add_word_boundaries_to_gloss(pred_y_no_stems, test_X)
    test_X = [seg_line_to_morphemes(seg_line, do_ignore_brackets = True, keep_word_boundaries = True) for seg_line in test_X]
    results = evaluate_system(test_y, pred_y, pred_y_no_stems, True, test_X, stem_dict)

    print_results_csv(results, OUTPUT_CSV_HEADER, OUTPUT_CSV, NO_RESULTS_MARKER)

if __name__ == '__main__':
    main()
