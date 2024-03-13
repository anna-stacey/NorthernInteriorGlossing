# For formatting fixes that can be done irrespective of language
# Ensuring that the glossing code doesn't need to worry about screening for these kinds of anomalies
import click
from gloss import read_datasets, sentence_to_glosses, sentence_to_morphemes, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY, ALL_BOUNDARIES_FOR_REGEX
import re
from glossed_data_utilities import NON_PERMITTED_PUNCTUATION, NON_PERMITTED_PUNCTUATION_REGEX

ALL_BOUNDARIES = [LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, REGULAR_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY]
NON_GLOSS_LINE_BOUNDARIES = [LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, CLITIC_BOUNDARY, REDUPLICATION_BOUNDARY]
ALL_BOUNDARIES_FOR_REGEX_SANS_CLOSERS = (ALL_BOUNDARIES_FOR_REGEX.replace("\}", "")).replace(">", "")
DOUBLE_BOUNDARY_REGEX = ALL_BOUNDARIES_FOR_REGEX + ALL_BOUNDARIES_FOR_REGEX
GLOSS_DOUBLE_BOUNDARY_REGEX = ALL_BOUNDARIES_FOR_REGEX_SANS_CLOSERS + ALL_BOUNDARIES_FOR_REGEX # To permit an exception - see data expectations in README for reasoning
DISCONNECTED_BOUNDARY_REGEX = ALL_BOUNDARIES_FOR_REGEX + "(\s|$)"
GLOSS_DISCONNECTED_BOUNDARY_REGEX = ALL_BOUNDARIES_FOR_REGEX_SANS_CLOSERS + "(\s|$)" # To permit an exception - see data expectations in README for reasoning
NON_PERMITTED_PUNCUTATION_TRANSCRIPTION_ONLY = ["="]
NON_PERMITTED_PUNCUTATION_TRANSCRIPTION_ONLY_REGEX = "[=]"

# Maintaining global test fail counts, so they can be tracked cumulatively across the train, dev, and test files
# General formatting tests
tab_fails = 0
multi_space_fails = 0
newline_fails = 0

# Tests relevant for both segmentation or glossing
seg_multi_boundary_fails = 0
seg_disconnected_morpheme_fails = 0
seg_infix_boundary_mismatch_fails = 0 # There can be multiple of these per line (currently flagging up to 1 <> error and up to 1 {} error)
seg_infix_boundary_misplacement_fails = 0 # There can be multiple of these per line (currently flagging up to 1 <> error and up to 1 {} error)
seg_non_permitted_punctuation_fails = 0

# Segmentation-specific tests
trans_seg_num_words_fails = 0
trans_non_permitted_punctuation_fails = 0

# Glossing-specific tests
gloss_multi_boundary_fails = 0
gloss_disconnected_morpheme_fails = 0
gloss_infix_boundary_mismatch_fails = 0 # There can be multiple of these per line (currently flagging up to 1 <> error and up to 1 {} error)
gloss_infix_boundary_misplacement_fails = 0 # There can be multiple of these per line (currently flagging up to 1 <> error and up to 1 {} error)
seg_gloss_num_words_fails = 0
seg_gloss_num_morphemes_fails = 0
seg_gloss_word_num_morphemes_fails = 0 # There can be multiple of these per line
gloss_boundary_marker_fails = 0
seg_gloss_boundary_fails = 0

# Takes in a dataset, and sends it off to various screening functions
# No return value -- just updates all our global fail counts
def screen_data(dataset, SEG_LINE_NUMBER, GLOSS_LINE_NUMBER):
    lines_per_sentence = len(dataset[0])

    for sentence in dataset:
        general_sentence_screen(sentence, lines_per_sentence)
        for line in sentence:
            general_screen(line)
        seg_screen(sentence[0], sentence[SEG_LINE_NUMBER])
        seg_and_gloss_screen(sentence[SEG_LINE_NUMBER])
        gloss_screen(sentence[SEG_LINE_NUMBER], sentence[GLOSS_LINE_NUMBER])

def general_sentence_screen(sentence, lines_per_sentence):
    if not (len(sentence) == lines_per_sentence):
        print("\nFatal error: The number of lines per sentence is inconsistent!")
        print(f"The first sentence had {lines_per_sentence} lines, which was set as the standard.  But the following sentence has {len(sentence)} lines:")
        print(sentence)
        print("Prescreening cannot proceed correctly until this is fixed, so the rest of the checks have been cancelled.")
        exit()

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

# Tests that are relevant only for segmentation
def seg_screen(transcription_line, seg_line):
    global trans_seg_num_words_fails
    global trans_non_permitted_punctuation_fails

    transcription_words = transcription_line.split()
    seg_words = seg_line.split()

    if len(transcription_words) != len(seg_words):
        print(f"\n- Error: the following line contains a mismatch between the number of *words* in the transcription and segmented lines.  The transcription line has {len(transcription_words)} words, whereas the segmented line has {len(seg_words)} words.")
        print("Transcription line:", transcription_line)
        print("Segmentation line:", seg_line)
        trans_seg_num_words_fails += 1

    if re.search(NON_PERMITTED_PUNCTUATION_REGEX, transcription_line) or re.search(NON_PERMITTED_PUNCUTATION_TRANSCRIPTION_ONLY_REGEX, transcription_line):
        print(f"\n- Error: the following transcription line contains non-permitted punctuation (i.e., one of {NON_PERMITTED_PUNCTUATION} or {NON_PERMITTED_PUNCUTATION_TRANSCRIPTION_ONLY}).")
        print(transcription_line)
        trans_non_permitted_punctuation_fails += 1

# Tests that are relevant whether your doing segmentation OR glossing
# (Note these are only *applied* to the seg line, but they're *relevant* for both processes)
def seg_and_gloss_screen(seg_line):
    global seg_multi_boundary_fails
    global seg_disconnected_morpheme_fails
    global seg_infix_boundary_mismatch_fails
    global seg_infix_boundary_misplacement_fails
    global seg_non_permitted_punctuation_fails

    if re.search(DOUBLE_BOUNDARY_REGEX, seg_line):
        print(f"\n- Error: the following segmentation line contains consecutive boundaries (i.e., at least two of f{ALL_BOUNDARIES} in immediate succession).")
        print(seg_line)
        seg_multi_boundary_fails += 1

    if re.search(DISCONNECTED_BOUNDARY_REGEX, seg_line):
        print(f"\n- Error: the following segmentation line contains a morpheme boundary not connected to two morphemes!")
        print(seg_line)
        seg_disconnected_morpheme_fails += 1

    if not infix_matching_boundaries_check(seg_line, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY):
        print(f"\n- Error: the following segmentation line contains an infix boundary (< or >) without a partner infix boundary in the right position.")
        print(seg_line)
        seg_infix_boundary_mismatch_fails += 1

    if not infix_matching_boundaries_check(seg_line, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY):
        print("\n- Error: the following segmentation line contains a reduplicating infix boundary ({ or }) without a partner infix boundary in the right position.")
        print(seg_line)
        seg_infix_boundary_mismatch_fails += 1

    if not infix_boundary_placement_check(seg_line, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, True):
        print(f"\n- Error: the following segmentation line contains an infix boundary (< or >) that was misplaced.")
        print(seg_line)
        seg_infix_boundary_misplacement_fails += 1

    if not infix_boundary_placement_check(seg_line, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, True):
        print("\n- Error: the following segmentation line contains a reduplicating infix boundary ({ or }) that was misplaced.")
        print(seg_line)
        seg_infix_boundary_misplacement_fails += 1

    if re.search(NON_PERMITTED_PUNCTUATION_REGEX, seg_line):
        print(f"\n- Error: the following segmentation line contains non-permitted punctuation (i.e., one of {NON_PERMITTED_PUNCTUATION}).")
        print(seg_line)
        seg_non_permitted_punctuation_fails += 1

# Check that infix boundaries are used as expected - i.e. in left/right pairs (<>) with no other boundaries in between
# Returns a boolean - true if no such errors found, false if at least one was found
def infix_matching_boundaries_check(line, left_boundary, right_boundary):
    check_passed = True
    words = line.split(" ")
    for word in words:
        if not check_passed: # You can quit early if we already found an issue to flag
            break
        # Ignore words that don't contain infixes at all
        if left_boundary in word or right_boundary in word:
            boundaries_list = re.findall(ALL_BOUNDARIES_FOR_REGEX, word)
            for i, boundary in enumerate(boundaries_list):
                # Left boundary must have a right boundary **immediately** to its right
                if boundary == left_boundary:
                    if (i == len(boundaries_list) - 1) or not (boundaries_list[i + 1] == right_boundary):
                        check_passed = False
                # Also want to flag any lone right boundaries
                # This means in cases where both boundaries are present but there's another interceding boundary, this error will occur twice (above and here)
                elif boundary == right_boundary:
                    if not (boundaries_list[i - 1] == left_boundary):
                        check_passed = False
    return check_passed

def infix_boundary_placement_check(line, left_boundary, right_boundary, is_seg_line):
    check_passed = True
    words = line.split(" ")

    for word in words:
        if not check_passed: # You can quit early if we already found an issue to flag
            break
        if is_seg_line:
            # In the seg line, an infix must be, well, infixed! So it should have a morpheme immediately on either side of the boundaries
            if left_boundary in word:
                left_boundary_pos = word.index(left_boundary)
                if left_boundary_pos - 1 < 0 or word[left_boundary_pos - 1] in ALL_BOUNDARIES:
                    check_passed = False
            if right_boundary in word:
                right_boundary_pos = word.index(right_boundary)
                if left_boundary_pos - 1 < 0 or word[left_boundary_pos - 1] in ALL_BOUNDARIES:
                    check_passed = False
        else:
            if left_boundary in word:
                left_boundary_pos = word.index(left_boundary)
                # The left boundary should immediately follow a morpheme, not a space or boundary!
                if left_boundary_pos - 1 < 0 or word[left_boundary_pos - 1] in ALL_BOUNDARIES:
                    check_passed = False
            if right_boundary in word:
                right_boundary_pos = word.index(right_boundary)
                # The right boundary *should* immediately precede a space or boundary, not a morpheme!
                if not (right_boundary_pos + 1 == len(word) or word[right_boundary_pos + 1] in ALL_BOUNDARIES):
                    check_passed = False

    return check_passed

# Tests that are relevant only for glossing
def gloss_screen(seg_line, gloss_line):
    global gloss_multi_boundary_fails
    global gloss_disconnected_morpheme_fails
    global gloss_infix_boundary_mismatch_fails
    global gloss_infix_boundary_misplacement_fails
    global gloss_boundary_marker_fails
    global seg_gloss_num_words_fails
    global seg_gloss_num_morphemes_fails
    global seg_gloss_word_num_morphemes_fails
    global seg_gloss_boundary_fails

    if re.search(GLOSS_DOUBLE_BOUNDARY_REGEX, gloss_line):
        print(f"\n- Error: the following gloss line contains consecutive boundaries (i.e., at least two of {ALL_BOUNDARIES} in immediate succession).")
        print("Gloss line:", gloss_line)
        gloss_multi_boundary_fails += 1

    if re.search(GLOSS_DISCONNECTED_BOUNDARY_REGEX, gloss_line):
        print(f"\n- Error: the following gloss line contains a morpheme boundary not connected to two morphemes!")
        print(gloss_line)
        gloss_disconnected_morpheme_fails += 1

    if not infix_matching_boundaries_check(gloss_line, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY):
        print(f"\n- Error: the following gloss line contains an infix boundary (< or >) without a partner infix boundary in the right position.")
        print(gloss_line)
        gloss_infix_boundary_mismatch_fails += 1

    if not infix_matching_boundaries_check(gloss_line, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY):
        print("\n- Error: the following gloss line contains a reduplicating infix boundary ({ or }) without a partner infix boundary in the right position.")
        print(gloss_line)
        gloss_infix_boundary_mismatch_fails += 1

    if not infix_boundary_placement_check(gloss_line, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY, False):
        print(f"\n- Error: the following gloss line contains an infix boundary (< or >) that is misplaced.")
        print(gloss_line)
        gloss_infix_boundary_misplacement_fails += 1

    if not infix_boundary_placement_check(gloss_line, LEFT_REDUP_INFIX_BOUNDARY, RIGHT_REDUP_INFIX_BOUNDARY, False):
        print("\n- Error: the following gloss line contains a reduplicating infix boundary ({ or }) that is misplaced.")
        print(gloss_line)
        gloss_infix_boundary_misplacement_fails += 1

    seg_words = seg_line.split(" ")
    gloss_words = gloss_line.split(" ")

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
    seg_morphemes = sentence_to_morphemes(seg_line, as_words = False)
    # Might modify gloss_line btw...
    gloss_morphemes = sentence_to_glosses(gloss_line)

    if len(seg_morphemes) != len(gloss_morphemes):
        print(f"\n- Error: the following line contains a mismatch between the number of *morphemes* in the segmented and gloss lines.  The segmented line has {len(seg_morphemes)} morphemes, whereas the gloss line has {len(gloss_morphemes)} morphemes.")
        print("Segmentation line:", seg_line)
        print("Gloss line:", gloss_line)
        # Uncomment this for more help identifying these problems!
        # for i, (seg_morph, gloss_morph) in enumerate(zip(seg_morphemes, gloss_morphemes)):
        #     print(f"Seg word #{i + 1}:\t", seg_morph)
        #     print(f"Gloss word #{i + 1}:\t", gloss_morph)
        seg_gloss_num_morphemes_fails += 1

    # A slightly more nuanced morpheme alignment check
    seg_morphemes_by_word = sentence_to_morphemes(seg_line, as_words = True)
    gloss_morphemes_by_word = sentence_to_morphemes(gloss_line, as_words = True)
    for i, (seg_word_with_morphemes, gloss_word_with_morphemes) in enumerate(zip(seg_morphemes_by_word, gloss_morphemes_by_word)):
        if len(seg_word_with_morphemes) != len(gloss_word_with_morphemes):
            print(f"\n- Error: the following line contains a mismatch between the number of *morphemes* in a word between the segmented and gloss lines.  The word {seg_morphemes_by_word[i]} at position {i} has {len(seg_word_with_morphemes)} morphemes in the segmented line, whereas in the gloss line it has {len(gloss_word_with_morphemes)} morphemes ({gloss_word_with_morphemes}).")
            print("Segmentation line:", seg_line)
            print("Gloss line:", gloss_line)
            seg_gloss_word_num_morphemes_fails += 1

    # Confirm that boundaries match between seg and gloss
    # (e.g. if a morpheme has a reduplication boundary in the segmentation line, then it does in the gloss line too)
    for seg_word, gloss_word in zip(seg_words, gloss_words):
        seg_boundaries = re.findall(ALL_BOUNDARIES_FOR_REGEX, seg_word)
        gloss_boundaries = re.findall(ALL_BOUNDARIES_FOR_REGEX, gloss_word)
        for seg_boundary, gloss_boundary in zip(seg_boundaries, gloss_boundaries):
            if seg_boundary != gloss_boundary:
                print(f"\n- Error: the following line contains a different boundary between the segmentation and gloss lines.  In the word {seg_word} '{gloss_word}', the segmentation line has a {seg_boundary} where the gloss line has a {gloss_boundary}.")
                print("Segmentation line:", seg_line)
                print("Gloss line:", gloss_line)
                seg_gloss_boundary_fails += 1

# No input value -- it just reads the global fail counts
# No return value -- just prints!
def print_screen_summary():
    all_fail_counts = [tab_fails, multi_space_fails, newline_fails, trans_non_permitted_punctuation_fails, seg_multi_boundary_fails, seg_disconnected_morpheme_fails, seg_infix_boundary_mismatch_fails, seg_infix_boundary_misplacement_fails, trans_seg_num_words_fails, seg_non_permitted_punctuation_fails, gloss_multi_boundary_fails, gloss_disconnected_morpheme_fails, gloss_infix_boundary_mismatch_fails, gloss_infix_boundary_misplacement_fails, seg_gloss_num_words_fails, seg_gloss_num_morphemes_fails, seg_gloss_word_num_morphemes_fails, gloss_boundary_marker_fails, seg_gloss_boundary_fails]
    total_fails = sum(all_fail_counts)
    print("\n --- Pre-screening summary: ---")
    print(f"{len(all_fail_counts)} different checks were run.")
    if total_fails == 0:
        print("No problems found in the dataset.  This data is ready to use!")
    else:
        print(f"There were {total_fails} problems in total:")
        # General tests
        print(f"    - {tab_fails} lines contained tab character(s).")
        print(f"    - {multi_space_fails} lines contained multiple spaces in a row.")
        print(f"    - {newline_fails} lines contained a newline character.")
        # Transcrption tests
        print(f"    - There were {trans_non_permitted_punctuation_fails} instances of non-permitted punctuation in the transcription line (i.e., one of {NON_PERMITTED_PUNCTUATION} or {NON_PERMITTED_PUNCUTATION_TRANSCRIPTION_ONLY}).")
        # Seg tests
        print(f"    - There were {seg_non_permitted_punctuation_fails} instances of non-permitted punctuation in the segmentation line (i.e., one of {NON_PERMITTED_PUNCTUATION}).")
        print(f"    - {trans_seg_num_words_fails} lines contained a different number of *words* between the transcription and segmented lines.")
        # Pairs of tests (one for seg, one for gloss)
        print(f"    - {seg_multi_boundary_fails} segmentation lines contained multiple boundaries in a row.")
        print(f"    - {gloss_multi_boundary_fails} gloss lines contained multiple boundaries in a row.")
        print(f"    - {seg_disconnected_morpheme_fails} segmentation lines contained a morpheme boundary that wasn't connected to a morpheme (on one side).")
        print(f"    - {gloss_disconnected_morpheme_fails} gloss lines contained a morpheme boundary that wasn't connected to a morpheme (on one side).")
        print(f"    - There were {seg_infix_boundary_mismatch_fails} instances in the segmentation line of an infix boundary whose partner infix boundary was absent or misplaced.")
        print(f"    - There were {gloss_infix_boundary_mismatch_fails} instances in the gloss line of an infix boundary whose partner infix boundary was absent or misplaced.")
        print(f"    - There were {seg_infix_boundary_misplacement_fails} instances in the segmentation line of an infix boundary that was inappropriately placed.")
        print(f"    - There were {gloss_infix_boundary_misplacement_fails} instances in the gloss line of an infix boundary that was inappropriately placed.")
        # Other glossy tests
        print(f"    - {gloss_boundary_marker_fails} lines contained a morpheme boundary in the gloss line other than the regular boundary marker (i.e., one of {NON_GLOSS_LINE_BOUNDARIES}).")
        print(f"    - {seg_gloss_num_words_fails} lines contained a different number of *words* between the segmented and gloss lines.")
        print(f"    - {seg_gloss_num_morphemes_fails} lines contained a different number of *morphemes* between the segmented and gloss lines.")
        print(f"    - There were {seg_gloss_word_num_morphemes_fails} instances of a different number of *morphemes* in a given *word* between the segmented and gloss lines.")
        print(f"    - There were {seg_gloss_boundary_fails} instances of a different kind of morpheme boundary between the segmented and gloss lines.")
    print("\n")

def get_gloss_inventory(all_data, segmentation_line_number, gloss_line_number):
    # Dictionary where the keys are glosses, and the values are also dicts with morpheme keys and count values
    # e.g. 3ERG: [es, s]
    gloss_dict = {}
    for sentence in all_data:
        seg_line = sentence[segmentation_line_number]
        gloss_line = sentence[gloss_line_number]
        morphemes = sentence_to_morphemes(seg_line, as_words = False)
        glosses = sentence_to_glosses(gloss_line)
        assert(len(morphemes) == len(glosses))
        for morpheme, gloss in zip(morphemes, glosses):
            assert(morpheme)
            # If there's no entry for the gloss, add a new one
            # If there is an entry, check if this morpheme is already listed
            # If not, add it
            if not (gloss in gloss_dict.keys()):
                gloss_dict.update({gloss: {morpheme: 1}})
            else: # Add to the existing entry
                existing_entry = (gloss_dict.get(gloss))
                if morpheme in existing_entry:
                    current_count = existing_entry[morpheme]
                    # Update the morpheme + count dictionary
                    existing_entry.update({morpheme: current_count + 1 })
                    # Then update the gloss entry (with this updated morpheme/count dict)
                    gloss_dict.update({gloss: existing_entry})
                else:
                    existing_entry.update({morpheme: 1})
                    gloss_dict.update({gloss: existing_entry})

    # Switch to a separate dict for grams and stems, and words that are not translated (e.g., English words, people's names)
    gram_dict = {}
    stem_dict = {}
    not_translated_dict = {}
    for entry in gloss_dict.items():
        gloss = entry[0]
        morphemes_with_counts = entry[1]
        if gloss.isupper():
            gram_dict.update({gloss: morphemes_with_counts})
        # If there's only one morpheme form, and it's identical to the gloss!
        elif len(morphemes_with_counts) == 1 and list(morphemes_with_counts.keys())[0] == gloss:
            not_translated_dict.update({gloss: morphemes_with_counts})
        else:
            stem_dict.update({gloss: morphemes_with_counts})

    # Alphabetize, then print the results!
    gram_list = sorted(gram_dict.items())
    stem_list = sorted(stem_dict.items())
    english_list = sorted(not_translated_dict.items())
    print("***** GLOSS INVENTORY *****")
    print("--- Grams: ---")
    print("Total number of unique gram glosses:", len(gram_list))
    for entry in gram_list:
        print(entry[0], ":", _format_morpheme_and_count_dict(entry[1]))
    print("\n\n--- Stems: ---")
    print("Total number of unique stem glosses:", len(stem_list))
    for entry in stem_list:
        print(entry[0], ":", _format_morpheme_and_count_dict(entry[1]))
    print("\n\n--- \"Stems\" that are just English/onomatopoeia: ---")
    print("Total number of such unique glosses:", len(english_list))
    for entry in english_list:
        print(entry[0], ":", _format_morpheme_and_count_dict(entry[1]))

def _format_morpheme_and_count_dict(dict):
    line_to_print = ""
    for entry in dict.items():
        line_to_print += entry[0] + " (" + str(entry[1]) + "), "

    line_to_print = re.sub(", $", "", line_to_print)
    return line_to_print

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
    print("\n***** PRESCREENING ******\n")
    print("--- Errors found in train dataset: ---")
    screen_data(train, segmentation_line_number, gloss_line_number)

    print("\n--- Errors found in dev dataset: ---")
    screen_data(dev, segmentation_line_number, gloss_line_number)
    
    print("\n--- Errors found in test dataset: ---")
    screen_data(test, segmentation_line_number, gloss_line_number)

    # Print the results
    print_screen_summary()

    get_gloss_inventory(train + dev + test, segmentation_line_number, gloss_line_number)

if __name__ == '__main__':
    main()