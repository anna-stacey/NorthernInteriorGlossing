import click
import re
import sklearn_crfsuite
from glossed_data_utilities import add_back_OOL_words, as_percent, handle_OOL_words, read_file, write_sentences, OUT_OF_LANGUAGE_LABEL, UNICODE_STRESS
from glossed_data_handling_utilities import gloss_line_to_morphemes, ignore_brackets, seg_line_to_morphemes, REGULAR_BOUNDARY, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, NON_INFIXING_BOUNDARIES, LANG_LABEL_SYMBOLS
from os import getcwd, mkdir, path
from unicodedata import normalize

GOLD_OUTPUT_FILE_NAME = "gloss_gold.txt"
ALL_BOUNDARIES_FOR_REGEX = "[<>\{\}\-=~]"
LANG_IS_LABELED = False

# Quick note: we are *always* removing brackets when glossing.
# This is to handle the glossing style where unrealized morphemes/pieces of morphemes
# appear in brackets in the segmentation line (we never expect these brackets to also appear in the gloss line).
# This is a concern of the segmentation stage, not the glossing stage.
# So we can just remove the brackets, e.g. treat náq̓ʷ-m[in][-t]-∅-s as náq̓ʷ-min-t-∅-s
# Let's run through why that is:
# - If the data doesn't use bracketed affixes, this does nothing.
# - If the data puts such affixes in brackets in the seg line,
#   then the glossing process can act as if the brackets aren't even there.
# - And, if the data uses brackets for *parts* of affixes (e.g., m[in]) above,
#   then it also make sense to remove the brackets there so the glossing process
#   has access to the full, regular morpheme (i.e., min).

def read_datasets(train_file, dev_file, test_file):
    train = read_file(train_file)
    dev = read_file(dev_file)
    test = read_file(test_file)
    return train, dev, test

# Returns the X and y lines from the dataset
def extract_X_and_y(dataset, segmentation_line_number, gloss_line_number):
    X = [sentence[segmentation_line_number] for sentence in dataset]
    y = [sentence[gloss_line_number] for sentence in dataset]

    return X, y

# Gets the word, as a list of morphemes, and the current morpheme's position
# This is done so we can look at the neighbouring morphemes and the word the morpheme is a part of
# Returns a dictionary of features for the current morpheme
def morpheme_to_features(word, i):
    ACUTE_ACCENT = "\u0301"

    morpheme = word[i]
    # Determine language label now, because it may need to be removed from this morpheme
    # Check the end of the word for a lang label, and remove it from this morpheme if needed
    if (word[-1])[-1] in LANG_LABEL_SYMBOLS:
        lang_label = word[-1][-1]
        if morpheme[-1] in LANG_LABEL_SYMBOLS:
            morpheme = morpheme[:-1]
    # Because of infixes, the end of the word may be part of the penultimate morpheme
    elif len(word) > 1 and (word[-2])[-1] in LANG_LABEL_SYMBOLS:
        lang_label = word[-2][-1]
        if morpheme[-1] in LANG_LABEL_SYMBOLS:
            morpheme = morpheme[:-1]
    else:
        lang_label = None

    # Features of the morpheme itself
    features = {
      "morpheme": morpheme.lower(),
      "morpheme[-3:]": morpheme[-3:].lower(),
      "morpheme_no_stress": re.sub(ACUTE_ACCENT,"", morpheme.lower())
    }

    # If it's not the first morpheme in the word
    if (i > 0):
        features.update({
            "-1_morpheme": word[i - 1].lower(),
            "first_morpheme": False
        })
    else:
        features.update({
            "-1_morpheme": "",
            "first_morpheme": True
        })

    # If it's not the last morpheme in the word
    if (i < len(word) - 1):
        features.update({
            "+1_morpheme": word[i + 1].lower(),
            "last_morpheme": False
        })
    else:
        features.update({
            "+1_morpheme": "",
            "last_morpheme": True
        })

    if lang_label:
        features.update({
            "lang_label": lang_label
        })

    return features

# Returns a list of features for each morpheme for each word in the given sentence
def seg_line_to_features(segmentation_line):
    # Get a list of words, which are in turn lists of morphemes
    preprocessed_sentence = seg_line_to_morphemes(segmentation_line, do_ignore_brackets = True, keep_word_boundaries = True)
    featureVectorList = []
    for word in preprocessed_sentence:
        for i in range(len(word)):
            featureVectorList.append(morpheme_to_features(word, i))

    return featureVectorList

# Gets each X and y into the right format for the model, and returns them
# Inputs:
#   X: a list with one entry per sentence, where each entry is a seg line (as a string)
#   y: a list with one entry per sentence, where each entry is a gloss line (as a string)
# Outputs:
#   X: a list with one entry per sentence, where each entry is a list of seg line morphemes, where each entry is a dict of features abt that morpheme
#   y: a list with one entry per sentence, where each entry is a list of gloss line morphemes, where each entry is just that morpheme (as a string)
def format_X_and_y(X, y):
    # What form of input do we need?
    # We need a morpheme-by-morpheme breakdown, with each morpheme in the form of a dictionary with features
    # Meanwhile, the gold-standard label for each morpheme is the corresponding entry in the gloss line

    # Get a list of training feature vectors (in the form of a list of lists by sentence)
    X = [seg_line_to_features(segmentation_line) for segmentation_line in X]

    # Get a list of the training labels - i.e. the gloss for each morpheme
    y = [gloss_line_to_morphemes(gloss_line) for gloss_line in y]

    # Now that we've used them for features like morpheme_1, we can remove OOL tokens altogether
    remove_OOL_from_X_or_y(X, is_X = True)
    remove_OOL_from_X_or_y(y, is_X = False)

    # Confirm that we either do or do not have language labels, as specified
    for sentence in X:
        for morpheme_as_features in sentence:
            if LANG_IS_LABELED:
                assert("lang_label" in morpheme_as_features.keys())
            else:
                assert(not("lang_label" in morpheme_as_features.keys()))

    return X, y

# Returns the prediction list
def run_crf(model, X, y):
    pred_y = model.predict(X)
    return pred_y

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
                        result = _get_simple_morpheme_level_accuracy(dev_y, (run_crf(crf, dev_X, dev_y)))
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
                    result = _get_simple_morpheme_level_accuracy(dev_y, (run_crf(crf, dev_X, dev_y)))
                    print(f"With {max_iter} (max.) iterations, the {alg} algorithm, and {min_freq + 1} minimum feature frequency: {result}")
                    if result > best_accuracy:
                        best_accuracy = result
                        best_max_iter = max_iter
                        best_alg = alg
                        best_min_freq = min_freq

    best_accuracy_percent = as_percent(best_accuracy)
    if best_alg == 'lbfgs' or best_alg == 'l2sgd':
        print(f"Best result: {best_accuracy_percent}% accuracy with {best_max_iter} (max.) iterations, using the {best_alg} algorithm with a c2 of {best_c2}, and with a minimum feature frequency of {best_min_freq + 1}.")
    else:
        print(f"Best result: {best_accuracy_percent}% accuracy with {best_max_iter} (max.) iterations, using the {best_alg} algorithm and with a minimum feature frequency of {best_min_freq + 1}.")

# Returns the accuracy value (for each morpheme)
# Expects a list of sentences as lists of morphemes
# This is a very simple check which should only be used for dev purposes.
# The actual evaluation checks are in the evaluation script.
def _get_simple_morpheme_level_accuracy(y, predicted_y):
    assert len(y) == len(predicted_y), f"Mismatch between length of gold glosses ({len(y)}) and length of predicted glosses ({len(predicted_y)})."
    total = 0
    wrong = 0
    for gold_label_line, predicted_label_line in zip(y, predicted_y):
        assert(len(gold_label_line) == len(predicted_label_line))
        for gold_label, predicted_label in zip(gold_label_line, predicted_label_line):
            total += 1
            if gold_label != predicted_label:
                wrong += 1

    accuracy = as_percent((total - wrong) / total) if total > 0 else 0
    return accuracy

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

# Look for (some kind of) match for a given stem morpheme in our stem_dict
# Returns None if no match found, otherwise returns the matching stem morpheme from the stem_dict
def match_stem(morpheme, stem_dict):
    match = None

    # First, try for an exact match
    if morpheme in stem_dict:
        match = morpheme

    # Otherwise -- try to find a close match
    # For now we will consider:
    # 1) e/ə ambiguity and 2) stress ambiguity
    # A simple way to do this: convert all ə to e and remove all stress, then check for equality
    modified_morpheme = _generalize_morpheme(morpheme)

    stems = list(stem_dict.keys())
    stem_index = 0
    # Loop until we find a match or run out of stems to consider
    while match == None and stem_index < len(stem_dict):
        stem = stems[stem_index]
        modified_stem = _generalize_morpheme(stem)
        if modified_morpheme == modified_stem:
            match = stem
        stem_index += 1

    return match

# Permits stress variation, and schwa vs. e variation
def _generalize_morpheme(morpheme):
    # Be able to handle NFC or NFD stress
    modified_morpheme = normalize('NFD', morpheme)
    modified_morpheme = modified_morpheme.replace(UNICODE_STRESS, "")
    # Once stress is removed, NFD vs NFC makes no difference!

    modified_morpheme = modified_morpheme.replace("ə", "e")

    return modified_morpheme

# Returns the predicted glosses
def gloss_stems(dev_X, interim_pred_dev_y, stem_dict):
    pred_dev_y = []
    known_stem_count = 0
    unknown_stem_count = 0
    for sentence, glossed_sentence in zip(dev_X, interim_pred_dev_y):
        pred_glossed_sentence = []
        for morpheme_features, predicted_gloss in zip(sentence, glossed_sentence):
            morpheme = morpheme_features["morpheme"]
            # Look at everything the CRF identified as a stem
            if predicted_gloss == "STEM":
                # Check for a match
                match = match_stem(morpheme, stem_dict)
                if match:
                    # We know this stem! Fill it in
                    predicted_gloss = stem_dict[match]
                    known_stem_count += 1
                else:
                    unknown_stem_count += 1
            pred_glossed_sentence.append(predicted_gloss)
        pred_dev_y.append(pred_glossed_sentence)
    
    total_stem_count = known_stem_count + unknown_stem_count
    print(f"In the test set, {as_percent(unknown_stem_count/total_stem_count)}% ({unknown_stem_count}/{total_stem_count}) of stems were not in the stem dictionary.")
    return pred_dev_y

# Trains and returns the dictionary and the CRF!
# As well as train_y formatted without stems, which is needed for the CRF to tune hyperparameters
def train_system(train_X, train_y):
    # Prepare the stem dictionary
    train_y_no_stems, stem_dict = deal_with_stems_helper(train_X, train_y)
    # Train the CRF model for bound morphemes
    # Using the best values found during hyperparameter tuning
    crf = create_crf(train_X, train_y_no_stems, 50, 'ap', 0, -1)
    
    return train_y_no_stems, stem_dict, crf

# Returns the glossed output pre- and post stem glossing,
# plus the gold output, all with boundaries re-added
def run_system(X, y, X_with_boundaries, crf, stem_dict):
    # Run the CRF model for bound morphemes
    interim_pred_y = run_crf(crf, X, y)

    # Take that prediction, and apply the stem dictionary to it
    pred_y = gloss_stems(X, interim_pred_y, stem_dict)

    # Evaluate the overall result
    pred_y = add_word_boundaries_to_gloss(pred_y, X_with_boundaries)

    return pred_y

# Inputs:
#   - gloss: a list of sentences, which are lists of glosses
#   - list_with_boundaries: a list of sentences, which are strings containing glosses or words with boundaries
#     This can be a segmented or glossed line, because all that we're using are its boundaries.
#     (You'll want to use the seg line for the pipeline's predictions, because that's what knows how we've split each word into morphemes...)
def add_word_boundaries_to_gloss(gloss, list_with_boundaries):
    assert(len(gloss) == len(list_with_boundaries)) # Same number of sentences

    updated_gloss = []
    updated_gloss_line = []
    for gloss_line, line_with_boundaries in zip(gloss, list_with_boundaries):
        line_with_boundaries = ignore_brackets(line_with_boundaries)
        # So now both lines are lists of items
        line_with_boundaries = line_with_boundaries.split()
        morpheme_index = 0
        # Go word by word
        for word in line_with_boundaries:
            # Confirm our assumptions about infixes being marked symmetrically
            assert(word.count(LEFT_INFIX_BOUNDARY) == word.count(RIGHT_INFIX_BOUNDARY))
            assert(word.count(LEFT_REDUP_INFIX_BOUNDARY) == word.count(RIGHT_REDUP_INFIX_BOUNDARY))

            # Determine how many morphemes are in the word by counting up all the boundaries
            morpheme_count = 0
            all_boundaries = NON_INFIXING_BOUNDARIES + [LEFT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY]
            for boundary in all_boundaries:
                morpheme_count += word.count(boundary)
            morpheme_count += 1

            # Go morpheme by morpheme
            word_glossed = []
            for j in range(morpheme_count):
                assert (morpheme_index) < len(gloss_line), f"Morpheme index ({morpheme_index}) has exceeded bounds for the following gloss line of length {len(gloss_line)}: {gloss_line}.  \nThe whole line is {line_with_boundaries}."
                word_glossed.append(gloss_line[morpheme_index])
                morpheme_index += 1
            updated_gloss_line.append(word_glossed)
        updated_gloss.append(updated_gloss_line)
        updated_gloss_line = []

    return updated_gloss

# Take the whole list of sentences (with transcription, seg, etc.) and replace one line with our predicted lines
def make_sentence_list_with_prediction(sentence_list, prediction_line_list, line_number_to_replace):
    new_sentence_list = []
    for sentence, predicted_line in zip(sentence_list, prediction_line_list):
        new_sentence = sentence.copy()
        new_sentence[line_number_to_replace] = predicted_line
        new_sentence_list.append(new_sentence)

    return new_sentence_list

# Input:
# 1. a list of the input seg lines, which are lists of words (with the boundaries in place!)
# 2. a list of predicted gloss lines, which are lists of words, which are lists of morphemes
# Output: a list of predicted gloss lines, which are lists of words, which are strings (where morphemes are connected by hyphens)
# i.e., go from ["dog", "s"] to "dog-s"
def reassemble_predicted_words(input_seg_line_list, pred_gloss_line_list):
    assert(len(input_seg_line_list) == len(pred_gloss_line_list))
    infix_closing_boundaries = [RIGHT_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY]
    new_gloss_line_list = []

    for seg_line, gloss_line in zip(input_seg_line_list, pred_gloss_line_list):
        assert(len(seg_line) == len(gloss_line))
        gloss_line_as_list_of_words = []
        for seg_word, gloss_word in zip(seg_line, gloss_line):
            # Put the gloss morphemes together into a word, connected by the boundaries from the input
            boundaries = re.findall(ALL_BOUNDARIES_FOR_REGEX, seg_word)
            # Check that we have the right number of boundaries for the number of gloss morphemes
            # The # of boundaries (excl. infix closers) should be one less than the # of gloss morphemes
            assert (len(boundaries) - boundaries.count(RIGHT_INFIX_BOUNDARY) - boundaries.count(RIGHT_REDUP_INFIX_BOUNDARY)) == (len(gloss_word) - 1), str(gloss_word) + " in " + str(gloss_line) + "\n# of boundaries: " + str(len(boundaries)) + "\n# of gloss morphemes: " + str(len(gloss_word))
            combined_gloss_word = gloss_word[0]
            boundary_index = 0
            for gloss_morpheme_index in range(1, len(gloss_word)):
                combined_gloss_word += boundaries[boundary_index]
                boundary_index += 1
                combined_gloss_word += gloss_word[gloss_morpheme_index]
                # If this morpheme is an infix, add the closing infix boundary now
                if boundary_index < len(boundaries) and boundaries[boundary_index] in infix_closing_boundaries:
                    combined_gloss_word += boundaries[boundary_index]
                    boundary_index += 1

            # We should have used all boundaries
            assert boundary_index == len(boundaries), str(gloss_line) + "\nBoundary index: " + str(boundary_index) + "\n# of boundaries: " + str(len(boundaries))

            gloss_line_as_list_of_words.append(combined_gloss_word)

        new_gloss_line_list.append(gloss_line_as_list_of_words)

    return new_gloss_line_list

# Takes a list of sentences, where each sentence contains the transcription line, segmentation line, etc.
# No return value, just creates and writes to an output file
def write_output_file(sentence_list, output_folder, output_file_name):
    # Create the output subdirectory, if it doesn't already exist
    dir_path = getcwd() + "/" + output_folder
    if not path.exists(dir_path):
        mkdir(dir_path)

    # And create the output file!
    write_sentences(sentence_list, dir_path + output_file_name)

# More complex version of write_simple_output_file, that formats in sigmorphon style
def write_sigmorphon_output_file(sentence_list, output_folder, file_name, segmentation_line_number, gloss_line_number, is_open_track):
    ORTHOG_LINE_MARKER = "\\t "
    SEG_LINE_MARKER = "\\m "
    GLOSS_LINE_MARKER = "\\g "
    TRANSLATION_LINE_MARKER = "\\l "

    # Format the sentences as required for sigmorphon evaluation
    sentence_list_to_print = []
    for sentence in sentence_list:
        # Grab each line + attach the corresponding line marker
        transcription_line = ORTHOG_LINE_MARKER + sentence[0] # Assuming the transcription line is the first line
        seg_line = SEG_LINE_MARKER + sentence[segmentation_line_number]
        gloss_line = GLOSS_LINE_MARKER + sentence[gloss_line_number]
        translation_line = TRANSLATION_LINE_MARKER + sentence[gloss_line_number + 1]  # Assuming the translation line follows the gloss line

        # Make all morpheme boundaries just a hyphen, so that the sigmorphon eval process recognizes them
        seg_line = re.sub(ALL_BOUNDARIES_FOR_REGEX, REGULAR_BOUNDARY, seg_line)
        gloss_line = re.sub(ALL_BOUNDARIES_FOR_REGEX, REGULAR_BOUNDARY, gloss_line)
        gloss_line = re.sub(REGULAR_BOUNDARY + REGULAR_BOUNDARY, REGULAR_BOUNDARY, gloss_line) # Because the gloss line can have consecutive boundaries due to infixes (e.g. crazy<PL>-1PL.II)

        # Put the sentence back together with the new formatting
        if is_open_track: # In the closed track, segmentation is not used
            new_sentence = [transcription_line, seg_line, gloss_line, translation_line]
        else:
            new_sentence = [transcription_line, gloss_line, translation_line]

        sentence_list_to_print.append(new_sentence)

    write_output_file(sentence_list_to_print, output_folder, file_name)

# Input: X or y, a list of sentences, where each sentence is a list of morphemes
# Output: X or y with any OOL morpheme removed
def remove_OOL_from_X_or_y(X_or_y, is_X):
    for sentence in X_or_y:
        morpheme_count = len(sentence)
        morpheme_index = 0
        while morpheme_index < morpheme_count:
            morpheme = sentence[morpheme_index]
            # Check if this item is OOL!
            if (is_X and _is_X_token_OOL(morpheme)) or ((not is_X) and _is_y_token_OOL(morpheme)):
                sentence.pop(morpheme_index)
                morpheme_count = len(sentence)
            else:
                morpheme_index += 1

def _is_X_token_OOL(X_token):
    return (X_token["morpheme"] == OUT_OF_LANGUAGE_LABEL or X_token["morpheme"] == OUT_OF_LANGUAGE_LABEL.lower())

def _is_y_token_OOL(y_token):
    return y_token == OUT_OF_LANGUAGE_LABEL

@click.command()
@click.option("--train_file", required = True, help = "The name of the file containing all sentences in the train set.")
@click.option("--dev_file", required = True, help = "The name of the file containing all sentences in the dev set.")
@click.option("--test_file", required = True, help = "The name of the file containing all sentences in the test set.")
@click.option("--output_folder", required = True, help = "The name of the folder where output files should be written to.")
@click.option("--output_file", required = True, help = "The name of the file where the predictions will be written to.")
@click.option("--segmentation_line_number", required = True, help = "The line that contains the segmented sentence.  For example if there are four lines each and the segmentation is the second line, this will be 2.")
@click.option("--gloss_line_number", required = True, help = "The line that contains the glossed sentence.  For example if there are four lines each and the gloss is the third line, this will be 3.")
def main(train_file, dev_file, test_file, output_folder, output_file, segmentation_line_number, gloss_line_number):
    # Convert right away to prevent off-by-one errors
    segmentation_line_number = int(segmentation_line_number) - 1
    gloss_line_number = int(gloss_line_number) - 1

    # Read the files and break them down into the three sets
    train, dev, test = read_datasets(train_file, dev_file, test_file)

    # Save the test set as-is for output-printing purposes
    original_test = test
    original_test_transcription_lines = list(sentence[0] for sentence in original_test)
    # Replace OOL tokens with just a generic label, so that they will be included generically as -1_morpheme type features
    # After feature generation, these OOL tokens will be removed altogether from X and y! Then they just get added back (as their full word form) when output-printing
    train, dev, test = handle_OOL_words([train, dev, test], replace = True)[:3]

    # Grab the appropriate lines from each sentence
    # X = seg lines, y = gloss lines
    train_X, train_y = extract_X_and_y(train, segmentation_line_number, gloss_line_number)
    dev_X, dev_y = extract_X_and_y(dev, segmentation_line_number, gloss_line_number)
    test_X, test_y  = extract_X_and_y(test, segmentation_line_number, gloss_line_number)

    # Save versions with boundaries (and without OOL tokens), so we can do word-level evaluation
    test_without_OOL = handle_OOL_words([test])[0]
    test_X_with_boundaries, test_y_with_boundaries  = extract_X_and_y(test_without_OOL, segmentation_line_number, gloss_line_number)

    # Format X as features, and y as labels (OOL tokens will be removed here too)
    train_X, train_y = format_X_and_y(train_X, train_y)
    dev_X, dev_y  = format_X_and_y(dev_X, dev_y)
    test_X, test_y  = format_X_and_y(test_X, test_y)

    # Train the whole system
    train_y_no_stems, stem_dict, crf = train_system(train_X, train_y)

    # Hyper-parameter tuning
    #test_crf(train_X, train_y_no_stems, dev_X, dev_y)

    # Generate the output
    pred_y = run_system(test_X, test_y, test_X_with_boundaries, crf, stem_dict)

    # Assemble output file of predictions
    # Reassemble the predicted morphemes into string lines
    pred_y_to_print = add_back_OOL_words(original_test_transcription_lines, reassemble_predicted_words([line.split() for line in test_X_with_boundaries], pred_y))
    # Take the original test set, and substitute in our predicted gloss lines
    test_with_predictions = make_sentence_list_with_prediction(original_test, pred_y_to_print, gloss_line_number)
    write_output_file(test_with_predictions, output_folder, output_file)
    # And create a file of the gold version, formatted the same way to permit comparison
    write_output_file(original_test, output_folder, GOLD_OUTPUT_FILE_NAME)

if __name__ == '__main__':
    main()
