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

# Returns the accuracy value
def get_accuracy(y, predicted_y):
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

# No return value, just prints mislabelled morphemes
# Just a reminder - 
# X = a list of lists of: all the features for each morpheme in a sentence
# y = a list of lists of: the gloss for each morpheme in a sentence
def print_mislabelled(X, y, pred_y):
    for input, gold_label, predicted_label in zip(X, y, pred_y):
        # To prevent an out of range error
        if len(gold_label) != len(predicted_label):
            print("Hmm.. morpheme count mismatch!")
        else:
            for i in (range(len(gold_label))): # Compare morpheme by morpheme
                if gold_label[i] != predicted_label[i]:
                    morpheme = input[i]["morpheme"]
                    print(f"For {morpheme}: predicted {predicted_label[i]}, actually {gold_label[i]}\n")


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
    print(f"Of {total_stem_count} total stems, {unknown_stem_count} or {round(unknown_stem_count/total_stem_count * 100, 2)}% were not in the stem dictionary.")
    return pred_dev_y

# No return value
def get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y):
    # Divide up the predictions and gold labels into stems and grams
    # We know which are stems at this point - they're labelled stem in the interim set
    pred_y_stems = []
    pred_y_grams = []
    y_stems = []
    y_grams = []
    # Go sentence by sentence
    for sentence_without_stems, sentence_with_stems, gold_sentence in zip(interim_pred_y, pred_y, y):
        # Morpheme by morpheme
        for gloss_without_stems, gloss_with_stems, gold_gloss in zip(sentence_without_stems, sentence_with_stems, gold_sentence):
            if gloss_without_stems == 'STEM': # It's a stem
                pred_y_stems.append(gloss_with_stems)
                y_stems.append(gold_gloss)
            else: # It's a gram
                pred_y_grams.append(gloss_without_stems)
                y_grams.append(gold_gloss)

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
def evaluate_system(X, y, crf, stem_dict):

    # Run the CRF model on the dev set
    interim_pred_y, interim_accuracy = run_crf(crf, X, y)
    print(f"\nAccuracy after using CRF model to gloss bound morhpemes: {round(interim_accuracy * 100, 2)}%.")

    # Take that prediction, and apply the stem dictionary to it
    pred_y = gloss_stems(X, interim_pred_y, stem_dict)
    print(f"Accuracy after also applying dictionary to gloss stems: {round(get_accuracy(y, pred_y) * 100, 2)}%.")

    # Results - check out mislabelled morphemes, and print by-stem and by-gram accuracy
    # print_mislabelled(X, y, pred_y)
    get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y)

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

    # Format X as features, and y as labels
    train_X, train_y = format_X_and_y(train_X, train_y, True)
    dev_X, dev_y  = format_X_and_y(dev_X, dev_y, False)
    test_X, test_y  = format_X_and_y(test_X, test_y, False)

    # Train the whole system
    train_y_no_stems, stem_dict, crf = train_system(train_X, train_y)

    # Hyper-parameter tuning
    #test_crf(train_X, train_y_no_stems, dev_X, dev_y)

    # Evaluate system
    evaluate_system(test_X, test_y, crf, stem_dict)

        
# Doing this so that I can export functions to pipeline.py
if __name__ == '__main__':
  main()
