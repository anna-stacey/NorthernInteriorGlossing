import click
import re
import sklearn_crfsuite
from split_dataset import read_file

def read_datasets(train_file, dev_file, test_file):
    train = read_file(train_file)
    dev = read_file(dev_file)
    test = read_file(test_file)
    return train, dev, test

# Returns the X and y lines from the dataset
def extract_X_and_y(dataset):
    X = [sentence[1] for sentence in dataset]
    y = [sentence[3] for sentence in dataset]

    return X, y

# Gets the word, as a list of morphemes, and the current morpheme's position
# This is done so we can look at the neighbouring morphemes and the word the morpheme is a part of
# Returns a dictionary of features for the current morpheme
def morpheme_to_features(word, i):
    morpheme = word[i]
    word_str = ""
    for each_morpheme in word:
        word_str += each_morpheme

    # Features of the morpheme itself
    features = {
      "morpheme": morpheme.lower(),
      "morpheme[-3:]": morpheme[-3:].lower(),
    }

    # If it's not the first morpheme in the word
    if (i > 0):
        features.update({
            "-1_morpheme": word[i - 1].lower()
        })

    # If it's not the last morpheme in the word
    if (i < len(word) - 1):
        features.update({
            "+1_morpheme": word[i + 1].lower()
        })

    return features

# Preprocessing steps that are done for BOTH the seg and gloss lines (i.e. X and y)
# Returns the updated sentence
def general_preprocess(sentence):
    #  To deal with weird underline char, as in G̲aldo'o, I am just removing it for now
    sentence = re.sub(r'\u0332', "", sentence)

    sentence = sentence.replace("\n", "")

    # Remove bracketed affixes (at least for now)
    sentence = re.sub(r'\[[^\]]*\]', "", sentence)

    return sentence 

# Break down each (transcription) sentence into "words",
# where each word is a list of morphemes (could be just one) - this is done for feature generation
# Returns the sentence as a word list instead
def sentence_to_words(sentence):
    word_list = []

    sentence = general_preprocess(sentence)

    for word in sentence.split(" "):
        morpheme_list = []
        # Split up morphemes
        morpheme_list = re.split(r'[-=]', word)
        word_list.append(morpheme_list)
    return word_list


# Returns a list of features for each morpheme for each word in the given sentence
def sentence_to_features(sentence):
    preprocessed_sentence = sentence_to_words(sentence)
    featureVectorList = []
    for word in preprocessed_sentence:
        for i in range(len(word)):
            featureVectorList.append(morpheme_to_features(word, i))

    return featureVectorList


# Returns a list of glosses (one for each morpheme in the sentence)
# Possible complications with capital letters, apostrophes
def sentence_to_glosses(gloss_line):
    gloss_line = general_preprocess(gloss_line)

    # Break apart line morpheme-by-morpheme
    gloss_line = re.split(r'[-=\s]', gloss_line)

    return gloss_line
    

# A  check to see if any lines have discrepancies in the number of morphemes (transcription line vs gloss line)
# At least for now, just remove these lines :(
# Maybe in future, could replace problematic words with a NULL word, to not lose the data
# Returns X and y with misaligned sentences removed
def misalignment_check(X, y):
    X_without_errors = []
    y_without_errors = []
    error_count = 0
    for transcription_line, gloss_line in zip(X, y):
        if len(transcription_line) != len(gloss_line):
            error_count += 1
            # print("ERROR: length mismatch in the following line:\n", gloss_line)
            # print(f"Transcription line has {len(transcription_line)} elements, whereas gloss line has {len(gloss_line)} elements.\n")
        else: # No errors!
            X_without_errors.append(transcription_line)
            y_without_errors.append(gloss_line)
    print(f"Removed {error_count} mis-aligned sentences, with {len(X) - error_count} sentences remaining.")
    return X_without_errors, y_without_errors

# Gets each X and y into the right format for the model, and returns them
def format_X_and_y(X, y, isTrain):
    # What form of input do we need?
    # We need a morpheme-by-morpheme breakdown, with each morpheme in the form of a dictionary with features
    # Meanwhile, the gold-standard label for each morpheme is the corresponding entry in the gloss line

    # Get a list of training feature vectors (in the form of a list of lists by sentence)
    X = [sentence_to_features(transcription_line) for transcription_line in X]

    # Get a list of the training labels - i.e. the gloss for each morpheme
    y = [sentence_to_glosses(gloss_line) for gloss_line in y]

    # Let's remove any lines with errors :(
    if(isTrain):
        X, y = misalignment_check(X, y)

    return X, y

# Returns the accuracy value (for each morpheme)
def get_accuracy(y, predicted_y):
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

# Returns the accuracy value - this version includes going word-by-word
def get_detailed_accuracy(y, predicted_y):
    assert(len(y) == len(predicted_y))
    total = 0
    wrong = 0
    skip_count = 0 

    for gold_label_line, predicted_label_line in zip(y, predicted_y):
        # There must be the same number of words in the gold and the predicted lines
        # (The number of words is not impacted by the segmentation task)
        if(len(gold_label_line) == len(predicted_label_line)):
            wrong_per_sentence = 0
            for gold_word, predicted_word in zip(gold_label_line, predicted_label_line):
                # The number of morphemes can vary in the gold word vs the predicted word
                # So this zip may end up skipping some morphemes if one word contains more
                for gold_label, predicted_label in zip(gold_word, predicted_word):
                    total += 1
                    if gold_label != predicted_label:
                        wrong += 1
                        wrong_per_sentence +=1
        else:
            skip_count += 1

    print(f"Accuracy calculation skipped {skip_count} lines due to word count mismatch.")
    assert(total > 0)
    accuracy = (total - wrong) / total
    return accuracy

# Just returns the value
def get_word_level_accuracy(y, predicted_y):
    assert(len(y) == len(predicted_y))
    total = 0
    wrong = 0
    skip_count = 0

    for gold_label_line, predicted_label_line in zip(y, predicted_y):
        wrong_per_sentence = 0
        # There must be the same number of words in the gold and the predicted lines
        # (The number of words is not impacted by the segmentation task)
        if(len(gold_label_line) == len(predicted_label_line)):
            for gold_word, predicted_word in zip(gold_label_line, predicted_label_line):
                total += 1
                is_correct = True
                # The number of morphemes can vary in the gold word vs the predicted word
                # So this zip may end up skipping some morphemes if one word contains more
                for gold_label, predicted_label in zip(gold_word, predicted_word):
                    if gold_label != predicted_label:
                        is_correct = False

                # Was the whole word correct?
                if not is_correct:
                    wrong += 1
        else:
            skip_count += 1

    print(f"Accuracy calculation skipped {skip_count} lines due to word count mismatch.")
    assert(total > 0)
    accuracy = (total - wrong) / total
    return accuracy

# Returns the predictions and the accuracy value
def run_crf(model, X, y):
    pred_y = model.predict(X)
    return pred_y, get_accuracy(y, pred_y)

# Returns the model itself (trained)
def create_crf(train_X, train_y, max_iter, alg, min_freq, c2):
    # There is an extra parameter (c2) for these algs
    if alg == 'lbfgs' or alg == 'l2sgd':
        # Initialize the CRF model:
        crf = sklearn_crfsuite.CRF(
        algorithm = alg,
        c2 = c2,
        max_iterations = max_iter,
        min_freq = min_freq,
        all_possible_transitions = True
        )
    else:
        # Initialize the CRF model:
        crf = sklearn_crfsuite.CRF(
            algorithm = alg,
            max_iterations = max_iter,
            min_freq = min_freq,
            all_possible_transitions = True
        )

    # Fit the model on the training data
    try: # This is because of a bug in sklearn_crfsuite
        crf.fit(train_X, train_y)
    except AttributeError:
        pass

    return crf

# No return value
# This function makes the model and does hyperparameter tuning!
def test_crf(train_X, train_y, dev_X, dev_y):
    possible_max_iter = [10, 50, 100]
    possible_algs = ['lbfgs', 'l2sgd', 'ap', 'pa', 'arow']
    # Apparently, the model will ignore features that *do not occur more than x times*
    # So I am adding one when I print these values to make this easier to understand
    possible_min_freq = [0, 1, 2]
    possible_c2 = [0.1, 0.5, 1, 2]
    best_accuracy = 0
    best_max_iter = -1
    best_alg = ""
    best_min_freq = -1
    best_c2 = -1
    for max_iter in possible_max_iter:
        for alg in possible_algs:
            for min_freq in possible_min_freq:
                # The c2 parameter only applies to two algorithms
                if alg == 'lbfgs' or alg == 'l2sgd':
                    for c2 in possible_c2:
                        # Create a crf model with these parameters
                        crf = create_crf(train_X, train_y, max_iter, alg, min_freq, c2)
                        # And see how the model does on the dev set
                        throwaway, result = run_crf(crf, dev_X, dev_y)
                        print(f"With {max_iter} (max.) iterations, the {alg} algorithm using a c2 of {c2}, and {min_freq + 1} minimum feature frequency: {result}")
                        if result > best_accuracy:
                            best_accuracy = result
                            best_max_iter = max_iter
                            best_alg = alg
                            best_min_freq = min_freq
                            best_c2 = c2
                else:
                    # Create a crf model with these parameters
                    crf = create_crf(train_X, train_y, max_iter, alg, min_freq, -1)
                    # And see how the model does on the dev set
                    throwaway, result = run_crf(crf, dev_X, dev_y)
                    print(f"With {max_iter} (max.) iterations, the {alg} algorithm, and {min_freq + 1} minimum feature frequency: {result}")
                    if result > best_accuracy:
                        best_accuracy = result
                        best_max_iter = max_iter
                        best_alg = alg
                        best_min_freq = min_freq

    best_accuracy_percent = round(best_accuracy * 100, 2)
    if best_alg == 'lbfgs' or best_alg == 'l2sgd':
        print(f"Best result: {best_accuracy_percent}% accuracy with {best_max_iter} (max.) iterations, using the {best_alg} algorithm with a c2 of {best_c2}, and with a minimum feature frequency of {best_min_freq + 1}.")
    else:
        print(f"Best result: {best_accuracy_percent}% accuracy with {best_max_iter} (max.) iterations, using the {best_alg} algorithm and with a minimum feature frequency of {best_min_freq + 1}.")

# Handles getting X in the right format
def print_mislabelled_helper(X, X_with_boundaries, y, pred_y):
    X_morpheme_list = []
    morphemes_by_sentence = []
    for sentence in X:
        for morpheme_features in sentence:
            morphemes_by_sentence.append(morpheme_features["morpheme"])
        X_morpheme_list.append(morphemes_by_sentence)
        morphemes_by_sentence = []
    X_morpheme_list = add_word_boundaries_to_gloss(X_morpheme_list, X_with_boundaries)
    print_mislabelled(X_morpheme_list, y, pred_y)


# No return value, just prints mislabelled morphemes
# Just a reminder - 
# X = a list of sentences, which are lists of words, which are lists of morphemes (just transcribed)
# y = a list of sentences, which are lists of words, which are lists of glosses (for each morpheme)
def print_mislabelled(X, y, pred_y):
    assert(len(X) == len(y))
    skip_count = 0

    # Sentence by sentence
    for input_line, gold_label_line, predicted_label_line in zip(X, y, pred_y):
        # Number of words should be consistent
        # If there's issues, this funciton is just meant to be informative, so we don't need to quit.
        # Let's just skip that line and flag it.
        if ((len(input_line) == len(gold_label_line)) and (len(input_line) == len(predicted_label_line))):
            # Word by word
            for input_word, gold_label_word, predicted_label_word in zip(input_line, gold_label_line, predicted_label_line):
                # Number of morphemes per word can vary (bc of segmentation) - but we still need to prevent an out of range error
                if len(gold_label_word) != len(predicted_label_word):
                    print("Hmm.. can't compare morphemes because the number of morphemes in this word isn't consistent between the gold and predicted lines!\n")
                else:
                    assert(len(input_word) == len(gold_label_word))
                    for input_morpheme, gold_label_morpheme, predicted_label_morpheme in zip(input_word, gold_label_word, predicted_label_word):
                            if gold_label_morpheme != predicted_label_morpheme:
                                print(f"For {input_morpheme}: predicted {predicted_label_morpheme}, actually {gold_label_morpheme}\n")
        else:
            skip_count += 1
        
    print(f"Mislabel check skipped {skip_count} line(s) due to misalignment.")

# Create dictionary, and replace their glosses with "STEM" for input to the CRF
# Returns the stem-less version and the stem dictionary created
def deal_with_stems(segmented_line, gloss_line):
    mini_stem_dict = {}
    gloss_line_for_crf = []
    # Find every stem, and add an entry for it to the dictionary
    # Presently, we define stem as a gloss that contains a lowercase letter
    for morpheme_features, gloss in zip(segmented_line, gloss_line):
        morpheme = morpheme_features["morpheme"]
        if re.search(r'[a-z]', gloss):
            # It's a stem!
            mini_stem_dict.update({
                morpheme: gloss
            })
            gloss_line_for_crf.append("STEM")
        else:
            gloss_line_for_crf.append(gloss)

    return gloss_line_for_crf, mini_stem_dict

# Calls deal_with_stems,
# But first handles scaling from the dataset level to the sentence level
# Returns the stem-less version and the stem dictionary created
def deal_with_stems_helper(segmented_lines_as_features, gloss_lines):
    gloss_lines_with_stems_replaced = []
    stem_dict = {}
    for segmented_line, gloss_line in zip(segmented_lines_as_features, gloss_lines):
        gloss_line_with_stem_replaced, mini_dict = deal_with_stems(segmented_line, gloss_line)
        gloss_lines_with_stems_replaced.append(gloss_line_with_stem_replaced)
        stem_dict.update(mini_dict)

    return gloss_lines_with_stems_replaced, stem_dict

# Returns the predicted glosses
def gloss_stems(dev_X, interim_pred_dev_y, stem_dict):
    pred_dev_y = []
    known_stem_count = 0
    unknown_stem_count = 0
    for sentence, glossed_sentence in zip(dev_X, interim_pred_dev_y):
        pred_glossed_sentence = []
        for morpheme_features, predicted_gloss in zip(sentence, glossed_sentence):
            morpheme = morpheme_features["morpheme"]
            if predicted_gloss == "STEM" and morpheme in stem_dict:
                known_stem_count += 1
                pred_glossed_sentence.append(stem_dict[morpheme])
            else:
                if predicted_gloss == "STEM":
                    unknown_stem_count += 1
                pred_glossed_sentence.append(predicted_gloss)
        pred_dev_y.append(pred_glossed_sentence)
    
    total_stem_count = known_stem_count + unknown_stem_count
    print(f"{unknown_stem_count}/{total_stem_count} total stems, or {round(unknown_stem_count/total_stem_count * 100, 2)}%, were not in the stem dictionary.")
    return pred_dev_y

# No return value
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

    print(f"Accuracy for stems: {round(get_accuracy(y_stems, pred_y_stems) * 100, 2)}%.")
    print(f"Accuracy for grams: {round(get_accuracy(y_grams, pred_y_grams) * 100, 2)}%.")

# Trains and returns the dictionary and the CRF!
# As well as train_y formatted without stems, which is needed for the CRF to tune hyperparameters
def train_system(train_X, train_y):
    # Prepare the stem dictionary
    train_y_no_stems, stem_dict = deal_with_stems_helper(train_X, train_y)
    # Train the CRF model for bound morphemes
    # Using the best values found during hyperparameter tuning
    crf = create_crf(train_X, train_y_no_stems, 50, 'ap', 0, -1)
    
    return train_y_no_stems, stem_dict, crf

# No return value
# Uses crf for bound morphemes, then dictionary for stems
def evaluate_system(X, y, X_with_boundaries, y_with_boundaries, crf, stem_dict):

    # Run the CRF model for bound morphemes
    interim_pred_y, interim_accuracy = run_crf(crf, X, y)

    # Take that prediction, and apply the stem dictionary to it
    pred_y = gloss_stems(X, interim_pred_y, stem_dict)

    # Evaluate the overall result
    y = add_word_boundaries_to_gloss(y, y_with_boundaries)
    pred_y = add_word_boundaries_to_gloss(pred_y, X_with_boundaries)
    print("\n** Accuracy scores: **")
    print(f"Morpheme-level accuracy: {round(get_detailed_accuracy(y, pred_y) * 100, 2)}%.\n")
    print(f"Word-level accuracy: {round(get_word_level_accuracy(y, pred_y) * 100, 2)}%.\n")

    # Results - print by-stem and by-gram accuracy, and check out mislabelled morphemes
    interim_pred_y = add_word_boundaries_to_gloss(interim_pred_y, X_with_boundaries)
    get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y)
    #print_mislabelled_helper(X, X_with_boundaries, y, pred_y)

# Inputs:
#   - gloss: a list of sentences, which are lists of glosses
#   - list_with_boundaries: a list of sentences, which are strings containing glosses or words with boundaries
#     This can be a segmented or glossed line, because all that we're using are its boundaries.
#     (You'll want to use the seg line for the pipeline's predictions, because that's what knows how we've split each word into morphemes...)
def add_word_boundaries_to_gloss(gloss, list_with_boundaries):
    assert(len(gloss) == len(list_with_boundaries))

    updated_gloss = []
    updated_gloss_line = []
    for gloss_line, gloss_line_with_boundaries in zip(gloss, list_with_boundaries):
        gloss_line_with_boundaries = general_preprocess(gloss_line_with_boundaries)
        # So now both lines are lists of items
        gloss_line_with_boundaries = gloss_line_with_boundaries.split()
        morpheme_index = 0
        # Go word by word
        for i, word in enumerate(gloss_line_with_boundaries):
            morpheme_count = word.count("=") + word.count("-") + 1
            word_glossed = []
            # Go morpheme by morpheme
            for j in range(morpheme_count):
                assert((morpheme_index) < len(gloss_line))
                word_glossed.append(gloss_line[morpheme_index])
                morpheme_index += 1
            updated_gloss_line.append(word_glossed)
        updated_gloss.append(updated_gloss_line)
        updated_gloss_line = []

    return updated_gloss

@click.command()
@click.option("--train_file", help = "The name of the file containing all sentences in the train set.")
@click.option("--dev_file", help = "The name of the file containing all sentences in the dev set.")
@click.option("--test_file", help = "The name of the file containing all sentences in the test set.")
def main(train_file, dev_file, test_file):
    # Read the files and break them down into the three sets
    train, dev, test = read_datasets(train_file, dev_file, test_file)

    # Grab the appropriate lines from each sentence
    train_X, train_y = extract_X_and_y(train)
    dev_X, dev_y = extract_X_and_y(dev)
    test_X, test_y  = extract_X_and_y(test)

    # Save versions with boundaries, so we can do word-level evaluation
    test_X_with_boundaries = test_X
    test_y_with_boundaries = test_y

    # Format X as features, and y as labels
    train_X, train_y = format_X_and_y(train_X, train_y, True)
    dev_X, dev_y  = format_X_and_y(dev_X, dev_y, False)
    test_X, test_y  = format_X_and_y(test_X, test_y, False)

    # Train the whole system
    train_y_no_stems, stem_dict, crf = train_system(train_X, train_y)

    # Hyper-parameter tuning
    #test_crf(train_X, train_y_no_stems, dev_X, dev_y)

    # Evaluate system
    evaluate_system(test_X, test_y, test_X_with_boundaries, test_y_with_boundaries, crf, stem_dict)

        
# Doing this so that I can export functions to pipeline.py
if __name__ == '__main__':
  main()
