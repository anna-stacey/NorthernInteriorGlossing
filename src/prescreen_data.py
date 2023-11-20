# For formatting fixes that can be done irrespective of language
# Ensuring that the glossing code doesn't need to worry about screening for these kinds of anomalies
import click
from gloss import read_datasets, sentence_to_glosses, sentence_to_words, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY
import re

ALL_BOUNDARIES = [LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY]
ALL_BOUNDARIES_REGEX = "<>\{\}\-=~"
NON_GLOSS_LINE_BOUNDARIES = [LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY]

# Maintaining global test fail counts, so they can be tracked cumulatively across the train, dev, and test files
# General formatting tests
tab_fails = 0
multi_space_fails = 0
newline_fails = 0

# Tests relevant for both segmentation or glossing
seg_multi_boundary_fails = 0
seg_disconnected_morpheme_fails = 0

# Glossing-specific tests
gloss_multi_boundary_fails = 0
seg_gloss_num_words_fails = 0
seg_gloss_num_morphemes_fails = 0
seg_gloss_word_num_morphemes_fails = 0 # There can be multiple of these per line
gloss_boundary_marker_fails = 0
seg_gloss_boundary_fails = 0

# Takes in a dataset, and sends it off to various screening functions
# No return value -- just updates all our global fail counts
def screen_data(dataset, seg_line_number, gloss_line_number):
    for sentence in dataset:
        for line in sentence:
            general_screen(line)
        seg_and_gloss_screen(sentence[seg_line_number])
        gloss_screen(sentence[seg_line_number], sentence[gloss_line_number])

# To be applied to every line!
def general_screen(line):
    global tab_fails
    global multi_space_fails
    global newline_fails

    if "\t" in line:
        print("\n- Error: the following line contains tab character(s).\n", line)
        tab_fails += 1

    if "  " in line:
        print("\n- Error: the following line contains multiple spaces in a row.\n", line)
        multi_space_fails += 1

    if "\n" in line:
        print("\n- Error: the following line contains a newline character.\n", line)
        newline_fails += 1

# Tests that are relevant whether your doing segmentation OR glossing
def seg_and_gloss_screen(seg_line):
    global seg_multi_boundary_fails
    global seg_disconnected_morpheme_fails

    double_boundary_regex = "[" + ALL_BOUNDARIES_REGEX + "][" + ALL_BOUNDARIES_REGEX + "]"
    if re.search(double_boundary_regex, seg_line):
        print(f"\n- Error: the following segmentation line contains consecutive boundaries (i.e., at least two of f{ALL_BOUNDARIES} in immediate succession).\n", seg_line)
        seg_multi_boundary_fails += 1

    disconnected_boundary_regex = "[" + ALL_BOUNDARIES_REGEX + "]" + "\s"
    if re.search(disconnected_boundary_regex, seg_line):
        print(f"\n- Error: the following segmentation line contains a morpheme boundary not connected to two morphemes!")
        print(seg_line)
        seg_disconnected_morpheme_fails += 1

# Tests that are relevant only for glossing
def gloss_screen(seg_line, gloss_line):
    global gloss_multi_boundary_fails
    global gloss_boundary_marker_fails
    global seg_gloss_num_words_fails
    global seg_gloss_num_morphemes_fails
    global seg_gloss_word_num_morphemes_fails
    global seg_gloss_boundary_fails

    # Only looking for a double boundary of the allowed boundary type (we're already checking for ANY instances of the non-permitted boundaries)
    double_boundary_regex = "[\\" + REGULAR_BOUNDARY + "][\\" + REGULAR_BOUNDARY + "]"
    if re.search(double_boundary_regex, gloss_line):
        print(f"\n- Error: the following gloss line contains consecutive boundaries (i.e., at least two of f{REGULAR_BOUNDARY} in immediate succession).")
        print("Gloss line:", gloss_line)
        gloss_multi_boundary_fails += 1

    seg_words = seg_line.split(" ")
    gloss_words = gloss_line.split(" ")

    # if any(boundary in gloss_line for boundary in NON_GLOSS_LINE_BOUNDARIES):
    #     print(f"\n- Error: the following line contains a morpheme boundary in the gloss line other than the regular boundary boundary.\n", gloss_line)
    #     gloss_boundary_marker_fails += 1

    if len(seg_words) != len(gloss_words):
        print(f"\n- Error: the following line contains a mismatch between the number of *words* in the segmented and gloss lines.  The segmented line has {len(seg_words)} words, whereas the gloss line has {len(gloss_words)} words.")
        print("Segmentation line:", seg_line)
        print("Gloss line:", gloss_line)
        # You can uncomment the below if you're having trouble identifying how the word mismatch is occurring
        # for i, (seg_word, gloss_word) in enumerate(zip(seg_words, gloss_words)):
        #     print(f"Seg word #{i + 1}:\t", seg_word)
        #     print(f"Gloss word #{i + 1}:\t", gloss_word)
        seg_gloss_num_words_fails += 1

    # These two functions I'm using from gloss.py are probably needlessly complicated and should be simplified
    seg_morphemes = [morpheme for word in sentence_to_words(seg_line) for morpheme in word]
    # Might modify gloss_line btw...
    gloss_morphemes = sentence_to_glosses(gloss_line)

    if len(seg_morphemes) != len(gloss_morphemes):
        print(f"\n- Error: the following line contains a mismatch between the number of *morphemes* in the segmented and gloss lines.  The segmented line has {len(seg_morphemes)} morphemes, whereas the gloss line has {len(gloss_morphemes)} morphemes.")
        print("Segmentation line:", seg_line)
        print("Gloss line:", gloss_line)
        seg_gloss_num_morphemes_fails += 1

    # A slightly more nuanced morpheme alignment check
    seg_morphemes_by_word = sentence_to_words(seg_line)
    gloss_morphemes_by_word = sentence_to_words(gloss_line)
    for i, (seg_word_with_morphemes, gloss_word_with_morphemes) in enumerate(zip(seg_morphemes_by_word, gloss_morphemes_by_word)):
        if len(seg_word_with_morphemes) != len(gloss_word_with_morphemes):
            print(f"\n- Error: the following line contains a mismatch between the number of *morphemes* in a word between the segmented and gloss lines.  The word {seg_morphemes_by_word[i]} at position {i} has {len(seg_word_with_morphemes)} morphemes in the segmented line, whereas in the gloss line it has {len(gloss_word_with_morphemes)} morphemes ({gloss_word_with_morphemes}).")
            print("Segmentation line:", seg_line)
            print("Gloss line:", gloss_line)
            seg_gloss_word_num_morphemes_fails += 1

    # # Confirm that boundaries match between seg and gloss
    # # (e.g. if a morpheme has a reduplication boundary in the segmentation line, then it does in the gloss line too)
    # for seg_word, gloss_word in zip(seg_words, gloss_words):
    #     seg_boundaries = re.findall("[" + ALL_BOUNDARIES_REGEX + "]", seg_word)
    #     gloss_boundaries = re.findall("[" + ALL_BOUNDARIES_REGEX + "]", gloss_word)
    #     for seg_boundary, gloss_boundary in zip(seg_boundaries, gloss_boundaries):
    #         if seg_boundary != gloss_boundary:
    #             print(f"\n- Error: the following line contains a different boundary between the segmentation and gloss lines.  In the word {seg_word} '{gloss_word}', the segmentation line has a {seg_boundary} where the gloss line has a {gloss_boundary}.")
    #             print("Segmentation line:", seg_line)
    #             print("Gloss line:", gloss_line)
    #             seg_gloss_boundary_fails += 1

# No input value -- it just reads the global fail counts
# No return value -- just prints!
def print_screen_summary():
    all_fail_counts = [tab_fails, multi_space_fails, newline_fails, seg_multi_boundary_fails, seg_disconnected_morpheme_fails, gloss_multi_boundary_fails, seg_gloss_num_words_fails, seg_gloss_num_morphemes_fails, seg_gloss_word_num_morphemes_fails, gloss_boundary_marker_fails, seg_gloss_boundary_fails]
    total_fails = sum(all_fail_counts)
    print("\n --- Pre-screening summary: ---")
    print(f"{len(all_fail_counts)} different checks were run.")
    if total_fails == 0:
        print("No problems found in the dataset.  This data is ready to use!")
    else:
        print(f"There were {total_fails} problems in total:")
        print(f"    - {tab_fails} lines contained tab character(s).")
        print(f"    - {multi_space_fails} lines contained multiple spaces in a row.")
        print(f"    - {newline_fails} lines contained a newline character.")
        print(f"    - {seg_multi_boundary_fails} segmentation lines contained multiple boundaries in a row.")
        print(f"    - {seg_disconnected_morpheme_fails} segmentation lines contained a morpheme boundary that wasn't connected to a morpheme (on one side).")
        print(f"    - {gloss_multi_boundary_fails} gloss lines contained multiple boundaries in a row.")
        print(f"    - {gloss_boundary_marker_fails} lines contained a morpheme boundary in the gloss line other than the regular boundary marker (i.e., one of {NON_GLOSS_LINE_BOUNDARIES}).")
        print(f"    - {seg_gloss_num_words_fails} lines contained a different number of *words* between the segmented and gloss lines.")
        print(f"    - {seg_gloss_num_morphemes_fails} lines contained a different number of *morphemes* between the segmented and gloss lines.")
        print(f"    - There were {seg_gloss_word_num_morphemes_fails} instances of a different number of *morphemes* in a given *word* between the segmented and gloss lines.")
        print(f"    - There were {seg_gloss_boundary_fails} instances of a different kind of morpheme boundary between the segmented and gloss lines.")

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

    # Screen each dataset!
    print("\n--- Errors found in train dataset: ---")
    screen_data(train, segmentation_line_number, gloss_line_number)

    print("\n--- Errors found in dev dataset: ---")
    screen_data(dev, segmentation_line_number, gloss_line_number)
    
    print("\n--- Errors found in test dataset: ---")
    screen_data(test, segmentation_line_number, gloss_line_number)

    # Print the results
    print_screen_summary()

if __name__ == '__main__':
    main()