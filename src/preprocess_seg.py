# Creates 9 files
# Input/output for train/dev/test = 2 x 3 = 6
# Then input/output for the pipeline (formatted slightly differently) = 2 + 1 summary file to reconstruct

import click
import re
from gloss import read_datasets, read_file
from os import getcwd, mkdir, path

OUTPUT_FOLDER = "/generated_data/"

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
    
# Convert from a list of sentences, to all the words in just one list
def sentence_list_to_word_list_with_summary(sentence_list):
    # Create the generated_data subdirectory, if it doesn't already exist
    dir_path = getcwd() + OUTPUT_FOLDER
    if not path.exists(dir_path):
        mkdir(dir_path)

    with open(dir_path + "pipeline_data_summary.txt", "w") as file:
        overall_list = []
        for sentence in sentence_list:
            word_count = 0
            for word in sentence:
                word_count += 1
                overall_list.append(word)
            file.write(str(word_count))
            file.write("\n")
        file.close()
    
    return overall_list

# Returns a list of words, where each word is a list of chars
def words_to_char_lists(word_list):
    new_list = []
    for word in word_list:
        word = list(word)
        new_list.append(word)

    return new_list
    
# Remove any sentences where misalignments are occurring
def sentence_check(sentence_list_a, sentence_list_b):
    new_list_a = []
    new_list_b= []
    original_length = len(sentence_list_a)
    for sentence_a, sentence_b in zip(sentence_list_a, sentence_list_b):
        if len(sentence_a) == len(sentence_b):
            new_list_a.append(sentence_a)
            new_list_b.append(sentence_b)

    updated_length = len(new_list_a)
    print(f"From {original_length} sentences, {updated_length} remain after mismatch checks.")
    return new_list_a, new_list_b


# Returns X and y formatted for fairseq
def format_data(X, y, forPipeline):
    # Convert each sentence to a list of words
    X_preprocessed = strings_to_word_lists(X, False)
    y_preprocessed = strings_to_word_lists(y, True)

    # In the pipeline use case, we can leave in misaligned sentences
    # because they will ultimately be evaluated post-gloss, sentence-by-sentence
    if not forPipeline:
        # Now is the perfect stage to pause and check X and y are matching up
        X_preprocessed, y_preprocessed = sentence_check(X_preprocessed, y_preprocessed)

    # We don't need sentence boundaries
    if forPipeline: # So we can later run the glossing model as well!
        X_preprocessed = sentence_list_to_word_list(X_preprocessed)
        y_preprocessed = sentence_list_to_word_list_with_summary(y_preprocessed)
    else:
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
    train_X_formatted, train_y_formatted = format_data(train_X, train_y, False)
    assert len(train_X_formatted) == len(train_y_formatted), f"\nX length: {len(train_X_formatted)} words.\ny length: {len(train_y_formatted)} words."
    create_file_of_words(train_X_formatted, "train.input")
    create_file_of_words(train_y_formatted, "train.output")

    dev_X_formatted, dev_y_formatted = format_data(dev_X, dev_y, False)
    assert(len(train_X_formatted) == len(train_y_formatted))
    create_file_of_words(dev_X_formatted, "dev.input")
    create_file_of_words(dev_y_formatted, "dev.output")

    test_X_formatted, test_y_formatted = format_data(test_X, test_y, False)
    assert(len(train_X_formatted) == len(train_y_formatted))
    create_file_of_words(test_X_formatted, "test.input")
    create_file_of_words(test_y_formatted, "test_gold.output")

    # When we run the entire pipeline, we will be evaluating post-gloss, sentence-by-sentence
    # In this case, misaligned sentences in the test set are not so destructive
    # So at least for now, we want a version of the test data that keeps these sentences in
    pipeline_X_full_formatted, pipeline_y_full_formatted = format_data(pipeline_X, pipeline_y, True)
    # No assert here - the counts may be different
    create_file_of_words(pipeline_X_full_formatted, "pipeline.input")
    create_file_of_words(pipeline_y_full_formatted, "pipeline_gold.output")   

if __name__ == '__main__':
    main()
