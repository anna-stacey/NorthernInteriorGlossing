# Creates 8 files
# Input/output for train/dev/test/pipeline = 2 x 4

import click
import re
from gloss import read_datasets, read_file
from os import getcwd, mkdir, path
from glossed_data_utilities import handle_OOL_words

OUTPUT_FOLDER = "/generated_data/"
TRAIN_INPUT_NAME = "train.input"
TRAIN_OUTPUT_NAME = "train.output"
DEV_INPUT_NAME = "dev.input"
DEV_OUTPUT_NAME = "dev.output"
TEST_INPUT_NAME = "test.input"
TEST_OUTPUT_NAME = "test.output"
PIPELINE_INPUT_NAME = "pipeline.input"
PIPELINE_OUTPUT_NAME = "pipeline.output"

# Given a list of words, creates a file where each word is on a new line, with spaces in between the chars
def create_file_of_words(list, file_name):
    # Create the generated_data subdirectory, if it doesn't already exist
    dir_path = getcwd() + OUTPUT_FOLDER
    if not path.exists(dir_path):
        mkdir(dir_path)

    with open(dir_path + file_name, "w") as file:
        for word in list:
            if len(word) > 0:
                for i, char in enumerate(word):
                    file.write(char)
                    if i < len(word) - 1: # non-final char
                        file.write(" ")
                    else: # final char - this should end the line
                        file.write("\n")
        file.close()

# Char removal that applies to both unsegmented and segmented lines
def general_preprocess(sentence, is_segmented):
    if is_segmented:
        # Remove bracketed affixes
        sentence = re.sub(r'\[[^\]]*\]', "", sentence)
    sentence = sentence.replace("\n", "")
    # Remove any double spaces that may be created from char removals
    sentence = re.sub(r'\s+', " ", sentence)

    sentence = sentence.lower()

    return sentence

# Go from a list of sentence strings, to a list of sentences which are lists of words
def strings_to_word_lists(dataset, is_segmented):
    sentences_list = []
    for sentence in dataset:
        sentence = general_preprocess(sentence, is_segmented)
        sentence = sentence.split(" ")
        sentences_list.append(sentence)

    return sentences_list

# Convert from a list of sentences, to all the words in just one list
def sentence_list_to_word_list(sentence_list):
    overall_list = []
    for sentence in sentence_list:
        for word in sentence:
            overall_list.append(word)
    
    return overall_list

# Returns a list of words, where each word is a list of chars
def words_to_char_lists(word_list):
    new_list = []
    for word in word_list:
        word = list(word)
        new_list.append(word)

    return new_list

# Returns X and y formatted for fairseq
def format_data(X, y):
    # Convert each sentence to a list of words
    X_preprocessed = strings_to_word_lists(X, False)
    y_preprocessed = strings_to_word_lists(y, True)

    X_preprocessed = sentence_list_to_word_list(X_preprocessed)
    y_preprocessed = sentence_list_to_word_list(y_preprocessed)

    # We want the words char by char
    X_preprocessed = words_to_char_lists(X_preprocessed)
    y_preprocessed = words_to_char_lists(y_preprocessed)

    return X_preprocessed, y_preprocessed

@click.command()
@click.option("--train_file", help = "The name of the file containing all sentences in the train set.")
@click.option("--dev_file", help = "The name of the file containing all sentences in the dev set.")
@click.option("--test_file", help = "The name of the file containing all sentences in the test set.")
@click.option("--pipeline_file", help = "The name of the file containing all sentences in the set to be used as input to the pipeline.")
def main(train_file, dev_file, test_file, pipeline_file):
    # Break down the data into three sets
    train, dev, test = read_datasets(train_file, dev_file, test_file)
    pipeline = read_file(pipeline_file)

    datasets = handle_OOL_words([train, dev, test])
    train, dev, test = datasets[:3]

    # Grab the lines we're interested in - unsegmented transcription for input, segmented orthographic transcription for output
    train_X = [sentence[0] for sentence in train]
    train_y = [sentence[1] for sentence in train]
    dev_X = [sentence[0] for sentence in dev]
    dev_y = [sentence[1] for sentence in dev]
    test_X = [sentence[0] for sentence in test]
    test_y = [sentence[1] for sentence in test]
    pipeline_X = [sentence[0] for sentence in pipeline]
    pipeline_y = [sentence[1] for sentence in pipeline]

    # Convert these to the appropriate format for fairseq
    train_X_formatted, train_y_formatted = format_data(train_X, train_y)
    assert len(train_X_formatted) == len(train_y_formatted), f"\nX length: {len(train_X_formatted)} words.\ny length: {len(train_y_formatted)} words."
    create_file_of_words(train_X_formatted, TRAIN_INPUT_NAME)
    create_file_of_words(train_y_formatted, TRAIN_OUTPUT_NAME)

    dev_X_formatted, dev_y_formatted = format_data(dev_X, dev_y)
    assert(len(dev_X_formatted) == len(dev_y_formatted))
    create_file_of_words(dev_X_formatted, DEV_INPUT_NAME)
    create_file_of_words(dev_y_formatted, DEV_OUTPUT_NAME)

    test_X_formatted, test_y_formatted = format_data(test_X, test_y)
    assert(len(test_X_formatted) == len(test_y_formatted))
    create_file_of_words(test_X_formatted, TEST_INPUT_NAME)
    create_file_of_words(test_y_formatted, TEST_OUTPUT_NAME)

    pipeline_X_full_formatted, pipeline_y_full_formatted = format_data(pipeline_X, pipeline_y)
    assert(len(pipeline_X_full_formatted) == len(pipeline_y_full_formatted))
    create_file_of_words(pipeline_X_full_formatted, PIPELINE_INPUT_NAME)
    create_file_of_words(pipeline_y_full_formatted, PIPELINE_OUTPUT_NAME)

    print("\nWrote to " + ", ".join([TRAIN_INPUT_NAME, TRAIN_OUTPUT_NAME, DEV_INPUT_NAME, DEV_OUTPUT_NAME, TEST_INPUT_NAME, TEST_OUTPUT_NAME, PIPELINE_INPUT_NAME]) + ", and " + PIPELINE_OUTPUT_NAME + ".\n")

if __name__ == '__main__':
    main()
