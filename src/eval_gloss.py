import click
from gloss import add_word_boundaries_to_gloss, deal_with_stems, extract_X_and_y, sentence_to_features, gloss_line_to_morphemes
from glossed_data_utilities import as_percent, handle_OOL_words, print_results_csv, read_file

OUTPUT_CSV = "./gloss_results.csv"
OUTPUT_CSV_HEADER = "Morpheme Acc,Word Acc,Stem Acc,Gram Acc"
NO_RESULTS_MARKER = None

# Returns scores (as percents)
def evaluate_system(y, pred_y, interim_pred_y):
    # Evaluate the overall result
    print("\n** Glossing accuracy: **")
    morpheme_acc = get_morpheme_level_accuracy(y, pred_y)
    print(f"Morpheme-level accuracy: {morpheme_acc}%.\n" if not(morpheme_acc == NO_RESULTS_MARKER) else "No morpheme-level accuracy because there are no morphemes!")
    word_acc = get_word_level_accuracy(y, pred_y)
    print(f"Word-level accuracy: {word_acc}%.\n" if not(word_acc == NO_RESULTS_MARKER) else "No word-level accuracy because there are no words!")

    # Results - print by-stem and by-gram accuracy
    stem_acc, gram_acc = get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y)
    print(f"Accuracy for stems: {stem_acc}%." if not(stem_acc == NO_RESULTS_MARKER) else "No stem accuracy because there are no stems!")
    print(f"Accuracy for grams: {gram_acc}%." if not(gram_acc == NO_RESULTS_MARKER) else "No gram accuracy because there are no grams!")

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
        assert len(gold_label_line) == len(predicted_label_line), f"Length mismatch! The gold line has {len(gold_label_line)} words, while the predicted line has {len(predicted_label_line)} words.\nGold line: {gold_label_line}\nPredicted line: {predicted_label_line}"
        wrong_per_sentence = 0
        for gold_word, predicted_word in zip(gold_label_line, predicted_label_line):
            # The number of morphemes can vary in the gold word vs the predicted word
            # So this check simply checks every *gold* morpheme
            for i, gold_label in enumerate(gold_word):
                total += 1
                if i >= len(predicted_word) or gold_label != predicted_word[i]:
                    wrong += 1
                    wrong_per_sentence +=1

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
def get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y):
    # Divide up the predictions and gold labels into stems and grams
    # We know which are stems at this point - they're labelled stem in the interim set
    pred_y_stems = []
    pred_y_grams = []
    y_stems = []
    y_grams = []
    # We need to build up the lists sentence-by-sentence, bc of the way evaluation works
    pred_y_stems_sentence = []
    pred_y_stems_word = []
    pred_y_grams_sentence = []
    pred_y_grams_word = []
    y_stems_sentence = []
    y_stems_word = []
    y_grams_sentence = []
    y_grams_word = []
    # Go sentence by sentence
    for sentence_without_stems, sentence_with_stems, gold_sentence in zip(interim_pred_y, pred_y, y):
        # Word by word
        for word_without_stems, word_with_stems, gold_word in zip(sentence_without_stems, sentence_with_stems, gold_sentence):
            # Morpheme by morpheme
            # This check is looking at what is *predicted* to be a stem or gram,
            # so we want to check every predicted morpheme, even if there's no corresponding gold morpheme!
            for i, (gloss_without_stems, gloss_with_stems) in enumerate(zip(word_without_stems, word_with_stems)):
                gold_gloss = gold_word[i] if i < len(gold_word) else ""
                if gloss_without_stems == 'STEM': # It's a stem
                    pred_y_stems_word.append(gloss_with_stems)
                    y_stems_word.append(gold_gloss)
                else: # It's a gram
                    pred_y_grams_word.append(gloss_without_stems)
                    y_grams_word.append(gold_gloss)

            # End of word reached; and it to our sentence and reset
            pred_y_stems_sentence.append(pred_y_stems_word)
            pred_y_grams_sentence.append(pred_y_grams_word)
            y_stems_sentence.append(y_stems_word)
            y_grams_sentence.append(y_grams_word)
            pred_y_stems_word = []
            pred_y_grams_word = []
            y_stems_word = []
            y_grams_word = []

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
    stem_acc = get_morpheme_level_accuracy(y_stems, pred_y_stems)
    gram_acc = get_morpheme_level_accuracy(y_grams, pred_y_grams)

    return stem_acc, gram_acc

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
    test_y = [gloss_line_to_morphemes(gloss_line, keep_word_boundaries = True) for gloss_line in test_y]
    pred_y = [gloss_line_to_morphemes(gloss_line, keep_word_boundaries = True) for gloss_line in pred_y]

    # Evaluate system
    # For stem/gram eval, we need a version of the predictions where all the stems are identified (in this case, by being glossed as just "STEM")
    pred_y_no_stems = [deal_with_stems((sentence_to_features(example[segmentation_line_number])), (gloss_line_to_morphemes(example[gloss_line_number])))[0] for example in predictions]
    # Calling deal_with_stems returns a pred_y without word boundaries, so add them back now to keep our results in a consistent format
    pred_y_no_stems = add_word_boundaries_to_gloss(pred_y_no_stems, test_X)
    results = evaluate_system(test_y, pred_y, pred_y_no_stems)

    print_results_csv(results, OUTPUT_CSV_HEADER, OUTPUT_CSV, NO_RESULTS_MARKER)

if __name__ == '__main__':
    main()
