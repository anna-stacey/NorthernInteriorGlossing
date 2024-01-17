import click
import re
import sklearn_crfsuite
from glossed_data_utilities import read_file, write_sentences
from os import getcwd, mkdir, path

OUTPUT_FOLDER = "/generated_data/"
GOLD_OUTPUT_FILE_NAME = "gloss_gold.txt"
PRED_OUTPUT_FILE_NAME = "gloss_pred.txt"

LEFT_INFIX_BOUNDARY = "<"
RIGHT_INFIX_BOUNDARY = ">"
LEFT_REDUP_INFIX_BOUNDARY = "{"
RIGHT_REDUP_INFIX_BOUNDARY = "}"
REGULAR_BOUNDARY = "-"
CLITIC_BOUNDARY = "="
REDUPLICATION_BOUNDARY = "~"
NON_INFIXING_BOUNDARIES = [REGULAR_BOUNDARY, REDUPLICATION_BOUNDARY, CLITIC_BOUNDARY]
ALL_BOUNDARIES_FOR_REGEX = "[<>\{\}\-=~]"

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

# We are removing the brackets but *leaving* the bracketed affix in
# This is to handle the glossing style where unrealized morphemes/pieces of morphemes
# appear in brackets.  This is a concern of the segmentation stage, not the glossing stage.
# So we can just remove the brackets, e.g. treat náq̓ʷ-m[in][-t]-∅-s as náq̓ʷ-min-t-∅-s
# Let's run through why that is:
# - If the data doesn't use bracketed affixes, this does nothing.
# - If the data puts such affixes in brackets in the seg line but not the gloss line,
#   then the glossing process can act as if the brackets aren't even there.
# - If the data puts such affixes in brackets in the seg line AND the gloss line,
#   then it's just regurgitating the brackets, so we can ignore them during the glossing
#   process and just add them back if printing the sentences.
# - And, if the data uses brackets for parts of affixes (e.g., m[in]) above,
#   then it also make sense to remove the brackets there so the glossing process
#   has access to the full, regular morpheme (i.e., min).
# This is the same as boundary types - the glossing process doesn't need to care
# if there's a - or = etc., but if we're printing our predictions we need to maintain them.
def ignore_brackets(sentence):
    sentence = re.sub(r'[\[\]]', "", sentence)
    return sentence 

# Given a segmentation line, return a list of its morphemes
# The as_words parameter specfies whether you want the returned morpheme list
# to be divided into word sub-lists
# For example:
# as_words = False, then it returns [w1m1, w1m2, w2m1, w2m2]
# as_words = True, then it returns [[w1m1, w1m2], [w2m1, w2m2]]
def sentence_to_morphemes(seg_line, as_words):
    morpheme_list = []
    if as_words:
        word_list = []

    seg_line = ignore_brackets(seg_line)

    for word in seg_line.split(" "):
        # Grab the morphemes from this current word
        morpheme_list += re.split(r"[" + re.escape("".join(NON_INFIXING_BOUNDARIES)) + r"]", word)
        # Infix marking requires special handling
        for i, morpheme in enumerate(morpheme_list):
            # Check for infixing
            if LEFT_INFIX_BOUNDARY in morpheme or LEFT_REDUP_INFIX_BOUNDARY in morpheme:
                assert(not (LEFT_INFIX_BOUNDARY in morpheme and LEFT_REDUP_INFIX_BOUNDARY in morpheme)) # If both occur in one word, we may have to add more complicated handling
                # Regular and redulicating infixing are handled the same way, but use different boundaries
                if LEFT_INFIX_BOUNDARY in morpheme:
                    breakdown_by_infix = morpheme.partition(LEFT_INFIX_BOUNDARY) # [firsthalfofmorpheme, <, infix>secondhalfofmorpheme]
                    first_half = breakdown_by_infix[0]
                    breakdown_by_infix = breakdown_by_infix[2].partition(RIGHT_INFIX_BOUNDARY) # infix, >, secondhalf
                    infix = breakdown_by_infix[0]
                    second_half = breakdown_by_infix[2]
                elif LEFT_REDUP_INFIX_BOUNDARY in morpheme:
                    breakdown_by_infix = morpheme.partition(LEFT_REDUP_INFIX_BOUNDARY) # [firsthalfofmorpheme, {, infix}secondhalfofmorpheme]
                    first_half = breakdown_by_infix[0]
                    breakdown_by_infix = breakdown_by_infix[2].partition(RIGHT_REDUP_INFIX_BOUNDARY) # infix, }, secondhalf
                    infix = breakdown_by_infix[0]
                    second_half = breakdown_by_infix[2]

                # Now, replace firsthalf<infix>secondhalf with [firsthalf+secondhalf, infix]
                # This matches how they're glossed! e.g. somestem-CRED
                morpheme_list.pop(i)
                morpheme_list.insert(i, first_half + second_half)
                morpheme_list.insert(i + 1, infix)

        # Prevent empty morphemes from being added
        while "" in morpheme_list:
            morpheme_list.remove("")

        if as_words and morpheme_list: # Only if non-empty (again, to avoid empty morphemes)
            word_list.append(morpheme_list)
            morpheme_list = []

    if as_words:
        return word_list
    else:
        return morpheme_list


# Returns a list of features for each morpheme for each word in the given sentence
def sentence_to_features(segmentation_line):
    # Get a list of words, which are in turn lists of morphemes
    preprocessed_sentence = sentence_to_morphemes(segmentation_line, as_words = True)
    featureVectorList = []
    for word in preprocessed_sentence:
        for i in range(len(word)):
            featureVectorList.append(morpheme_to_features(word, i))

    return featureVectorList


# Returns a list of glosses (one for each morpheme in the sentence)
def sentence_to_glosses(gloss_line):
    gloss_line = ignore_brackets(gloss_line)
    # Recall that infix boundaries aren't so complex to handle in the gloss line (just gloss1<gloss2>-gloss3)
    # We can just replace them with regular boundaries here, so they'll get handled by the re.split line
    gloss_line = re.sub(r"[" + LEFT_INFIX_BOUNDARY + "\\" + LEFT_REDUP_INFIX_BOUNDARY + "]", REGULAR_BOUNDARY, gloss_line)
    gloss_line = re.sub(r"[" + RIGHT_INFIX_BOUNDARY + "\\" + RIGHT_REDUP_INFIX_BOUNDARY + "]", "", gloss_line)

    # Break apart line morpheme-by-morpheme
    gloss_line = re.split(r"[" + re.escape("".join(NON_INFIXING_BOUNDARIES)) + "\s" + r"]", gloss_line)

    return gloss_line

# Gets each X and y into the right format for the model, and returns them
def format_X_and_y(X, y):
    # What form of input do we need?
    # We need a morpheme-by-morpheme breakdown, with each morpheme in the form of a dictionary with features
    # Meanwhile, the gold-standard label for each morpheme is the corresponding entry in the gloss line

    # Get a list of training feature vectors (in the form of a list of lists by sentence)
    X = [sentence_to_features(segmentation_line) for segmentation_line in X]

    # Get a list of the training labels - i.e. the gloss for each morpheme
    y = [sentence_to_glosses(gloss_line) for gloss_line in y]

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
    print(f"In the test set, {unknown_stem_count}/{total_stem_count} total stems, or {round(unknown_stem_count/total_stem_count * 100, 2)}%, were not in the stem dictionary.")
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

    # Results - print by-stem and by-gram accuracy
    interim_pred_y = add_word_boundaries_to_gloss(interim_pred_y, X_with_boundaries)
    get_accuracy_by_stems_and_grams(interim_pred_y, pred_y, y)

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
                assert((morpheme_index) < len(gloss_line))
                word_glossed.append(gloss_line[morpheme_index])
                morpheme_index += 1
            updated_gloss_line.append(word_glossed)
        updated_gloss.append(updated_gloss_line)
        updated_gloss_line = []

    return updated_gloss

# Take the whole list of sentences (with transcription, seg, etc.) and replace the gloss line with our predicted glosses
def make_output_file(sentence_list, file_name, gloss_pred_list, segmentation_line_number, gloss_line_number, isOpenTrack):
    new_sentence_list = []
    for sentence, pred_gloss_line in zip(sentence_list, gloss_pred_list):
        new_sentence = []
        new_sentence.extend(sentence[0:gloss_line_number])
        new_sentence.append(reassemble_gloss_line(pred_gloss_line))
        new_sentence.extend(sentence[gloss_line_number + 1:len(sentence)])

        new_sentence_list.append(new_sentence)

    # Now that it's formatted correctly, we can write the output file
    write_output_file(new_sentence_list, file_name, segmentation_line_number, gloss_line_number, isOpenTrack)

# Given the gloss line as a list of words, each containing lists of morpheme glosses, convert this to just a single string representing the sentence
def reassemble_gloss_line(line):
    sentence_as_list_of_words = []
    for word in line:
        new_word = "-".join(word)
        sentence_as_list_of_words.append(new_word)

    sentence_as_string = " ".join(sentence_as_list_of_words)

    return sentence_as_string

# Takes a list of sentences, where each sentence contains the transcription line, segmentation line, etc.
# No return value, just creates and write to an output file
def write_output_file(sentence_list, file_name, segmentation_line_number, gloss_line_number, isOpenTrack):
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
        if isOpenTrack: # In the closed track, segmentation is not used
            new_sentence = [transcription_line, seg_line, gloss_line, translation_line]
        else:
            new_sentence = [transcription_line, gloss_line, translation_line]

        sentence_list_to_print.append(new_sentence)

    # Create the output subdirectory, if it doesn't already exist
    dir_path = getcwd() + OUTPUT_FOLDER
    if not path.exists(dir_path):
        mkdir(dir_path)

    # And create the output file!
    write_sentences(sentence_list_to_print, dir_path + "/" + file_name)

@click.command()
@click.option("--train_file", help = "The name of the file containing all sentences in the train set.")
@click.option("--dev_file", help = "The name of the file containing all sentences in the dev set.")
@click.option("--test_file", help = "The name of the file containing all sentences in the test set.")
@click.option("--segmentation_line_number", help = "The line that contains the segmented sentence.  For example if there are four lines each and the segmentation is the second line, this will be 2.")
@click.option("--gloss_line_number", help = "The line that contains the glossed sentence.  For example if there are four lines each and the gloss is the third line, this will be 3.")
def main(train_file, dev_file, test_file, segmentation_line_number, gloss_line_number):
    # Convert right away to prevent off-by-one errors
    segmentation_line_number = int(segmentation_line_number) - 1
    gloss_line_number = int(gloss_line_number) - 1

    # Read the files and break them down into the three sets
    train, dev, test = read_datasets(train_file, dev_file, test_file)

    # Grab the appropriate lines from each sentence
    # X = seg lines, y = gloss lines
    train_X, train_y = extract_X_and_y(train, segmentation_line_number, gloss_line_number)
    dev_X, dev_y = extract_X_and_y(dev, segmentation_line_number, gloss_line_number)
    test_X, test_y  = extract_X_and_y(test, segmentation_line_number, gloss_line_number)

    # Save versions with boundaries, so we can do word-level evaluation
    test_X_with_boundaries = test_X
    test_y_with_boundaries = test_y

    # Format X as features, and y as labels
    train_X, train_y = format_X_and_y(train_X, train_y)
    dev_X, dev_y  = format_X_and_y(dev_X, dev_y)
    test_X, test_y  = format_X_and_y(test_X, test_y)

    # Train the whole system
    train_y_no_stems, stem_dict, crf = train_system(train_X, train_y)

    # Hyper-parameter tuning
    #test_crf(train_X, train_y_no_stems, dev_X, dev_y)

    # Evaluate system
    # Run our own evaluation
    pred_y = evaluate_system(test_X, test_y, test_X_with_boundaries, test_y_with_boundaries, crf, stem_dict)
    # Prepare for the sigmorphon evaluation
    # Assemble output file of predictions
    isOpenTrack = True # Because we had the segmentation to work with in this case!
    make_output_file(test, PRED_OUTPUT_FILE_NAME, pred_y, segmentation_line_number, gloss_line_number, isOpenTrack)
    # And create a file of the gold version, formatted the same way to permit comparison
    write_output_file(test, GOLD_OUTPUT_FILE_NAME, segmentation_line_number, gloss_line_number, isOpenTrack)

if __name__ == '__main__':
    main()
