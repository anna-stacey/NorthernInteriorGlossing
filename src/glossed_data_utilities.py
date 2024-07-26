# *** Common functions for creating train/dev/tests datasets ***
from os import mkdir, path
from random import shuffle
import re
from unicodedata import normalize

# Applies to the transcription and seg line.  Obviously periods are used a lot in the gloss line.
# Note that double colons (::) are being permitted b/c the St́át́imcets data seems to use them legitiamtely as a vowel length thing
NON_PERMITTED_PUNCTUATION_TRANSCRIPTION_SEG = [".", ",", "?", "\"", "“", "”", "`", "!", "♪", ":", ";", "–"] # Note this last one is not a regular hyphen!
NON_PERMITTED_PUNCTUATION_TRANSCRIPTION_SEG_REGEX = "[\.,\?\"“”`!♪;–]|([^:]):([^:]|$)" # Any of these characters, but including only *single* colons, not two in a row
PUNCTUATION_TO_IGNORE = "\.|,|\?|!|:"

OUT_OF_LANGUAGE_MARKER = "*"
OUT_OF_LANGUAGE_LABEL = "OOL"
DOUBLE_OOL_MARKER_REGEX = "\*[\*]+"

CLITIC_BOUNDARY = "="
NUMBER_OF_LINES = 4
UNICODE_STRESS = "\u0301"

# Returns a list of examples (where each example is a list containing the transcription, seg, etc. lines)
def read_file(file_path):
    with open(file_path) as f:
        lines = f.readlines()

        # In order to ensure the final example gets handled like the rest, we need to make sure that
        # the last line of content also ends in a "\n" (like every other line), and that there is a
        # "\n" line after the last bit of content
        # However, we also need to be sure that there are not additional newlines at EOF,
        # or we'll get blank "examples"

        # Ensure the last line of content ends with a "\n" for consistency
        if not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"

        # Remove any number of blank lines at EOF
        while lines[-1] == "\n":
            lines = lines[:len(lines) - 1]

        # Then add in one blank line, so we know the outcome is always exactly one blank line
        # (it actually seems that readlines() does not read in the final blank line)
        lines.append("\n")

    sentences = []
    current_sentence = []
    for i, line in enumerate(lines):
         # After each example is a blank line marking the end of the current sentence
         # Whenever we get there, it's time to add the present example to our list
        if line == "\n":
            sentences.append(current_sentence)
            current_sentence = []
        else:
            # Check for trailing whitespace, which should be removed
            line = line.strip()
            current_sentence.append(line)

    return(sentences)

# Takes a list of sentences, each of which is a list of transcription line, seg line, etc.
# Returns the list in the same format, just tidied!
def tidy_dataset(dataset):
    updated_dataset = []
    for sentence in dataset:
        updated_sentence = []
        for i, line in enumerate(sentence):
            # Remove commas, periods, and question marks from the seg and transcription lines
            if i == 0 or i == 1:
                line = re.sub(NON_PERMITTED_PUNCTUATION_TRANSCRIPTION_SEG_REGEX, r"\1\2", line)

            # Find 2+ spaces, and replace them with only one space
            line = re.sub(r"[ ]+[ ]+", " ", line)
            # Find sentence-initial or -final spaces, and remove them
            line = re.sub(r"^ ", "", line)
            line = re.sub(r" $", "", line)


            updated_sentence.append(line)
        updated_dataset.append(updated_sentence)
        updated_sentence = []

    return updated_dataset

# Fix the issue of clitics which are standalone in the orthographic line, but attached to a larger word in the segmentation and gloss lines
# Solution: Make it standalone in the seg and gloss lines too (to prevent altering the orthographic line)
def handle_clitics(data, pre_clitics, double_pre_clitics, post_clitics, double_post_clitics):
    updated_data = []
    for example in data:
        ortho_line = example[0]
        seg_line = example[1]
        gloss_line = example[2]
        # Grab all the words in the orthography line, so we can look for clitics as words there
        # Remove punctuation so it doesn't get in the way of looking for the particular clitic
        ortho_line_word_list = (re.sub(PUNCTUATION_TO_IGNORE, "", ortho_line)).split()
        seg_line_word_list = seg_line.split()
        gloss_line_word_list = gloss_line.split()
        # We're going to look word-by-word in the seg line
        for seg_word_index, seg_word in enumerate(seg_line_word_list):
            possibly_more_pre_clitics = True
            possibly_more_post_clitics = True
            while possibly_more_pre_clitics:
                # SINGLE PROCLITIC CHECK
                # Does the seg word start with a clitic from our list, connected with a '='?
                clitic_check = seg_word.partition(CLITIC_BOUNDARY)
                # If there was indeed an equals sign, and a proclitic before it
                if clitic_check[1] != "" and clitic_check[0] in pre_clitics.keys():
                    clitic = clitic_check[0]
                    word_without_clitic = clitic_check[2]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    # This check is quite strict -
                    # It will prevent problems with the wrong word being looked at, but it's also going to (at present)
                    # exclude a lot of problematic lines from being fixed. Something to think about...
                    if len(ortho_line_word_list) > seg_word_index and ortho_line_word_list[seg_word_index].lower() == pre_clitics[clitic] and word_without_clitic != "":
                        # Confirmed: we've found a clitic to fix!
                        # Now we need to modify the seg and gloss lines
                        assert len(seg_line_word_list) == len(gloss_line_word_list), f"Error: There are {len(seg_line_word_list)} words in the seg line, but {len(gloss_line_word_list)} words in the gloss line! \nSeg line word list: {seg_line_word_list}"

                        # Replace the seg word with two words - leaving the clitic standalone
                        seg_line_word_list.pop(seg_word_index)
                        seg_line_word_list.insert(seg_word_index, clitic)
                        seg_line_word_list.insert(seg_word_index + 1, word_without_clitic)

                        # Replace the *gloss* word with two words - leaving the clitic standalone
                        removed_gloss_word = gloss_line_word_list.pop(seg_word_index)
                        removed_gloss_split = removed_gloss_word.partition(CLITIC_BOUNDARY)
                        gloss_line_word_list.insert(seg_word_index, removed_gloss_split[0])
                        gloss_line_word_list.insert(seg_word_index + 1, removed_gloss_split[2])

                        # Update the current word and its position, for the sake of the while loop
                        seg_word = word_without_clitic
                        seg_word_index += 1
                    else:
                        possibly_more_pre_clitics = False

                # DOUBLE PROCLITIC CHECK
                # Repeat, but this time for the DOUBLE clitics
                double_clitic_check = clitic_check[2].partition(CLITIC_BOUNDARY)
                # Reassemble, around this SECOND equals sign
                clitic_check = (clitic_check[0] + CLITIC_BOUNDARY + double_clitic_check[0], CLITIC_BOUNDARY, double_clitic_check[2])
                if clitic_check[1] != "" and clitic_check[0] in double_pre_clitics.keys():
                    clitic = clitic_check[0]
                    word_without_clitic = clitic_check[2]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    # This check is quite strict -
                    # It will prevent problems with the wrong word being looked at, but it's also going to (at present)
                    # exclude a lot of problematic lines from being fixed. Something to think about...
                    if len(ortho_line_word_list) > seg_word_index and ortho_line_word_list[seg_word_index] == double_pre_clitics[clitic] and word_without_clitic != "":
                        # Okay, now we need to modify the seg and gloss lines
                        assert len(seg_line_word_list) == len(gloss_line_word_list), f"Error: There are {len(seg_line_word_list)} words in the seg line, but {len(gloss_line_word_list)} words in the gloss line! \nSeg line word list: {seg_line_word_list}"

                        # Replace this word in the list with two words, separating the clitic
                        seg_line_word_list.pop(seg_word_index)
                        seg_line_word_list.insert(seg_word_index, clitic)
                        seg_line_word_list.insert(seg_word_index + 1, word_without_clitic)

                        # Split the gloss
                        removed_gloss_word = gloss_line_word_list.pop(seg_word_index)
                        removed_gloss_split = removed_gloss_word.partition(CLITIC_BOUNDARY)
                        double_removed_gloss_split = removed_gloss_split[2].partition(CLITIC_BOUNDARY)
                        removed_gloss_split = (removed_gloss_split[0] + CLITIC_BOUNDARY + double_removed_gloss_split[0], CLITIC_BOUNDARY, double_removed_gloss_split[2])
                        gloss_line_word_list.insert(seg_word_index, removed_gloss_split[0])
                        gloss_line_word_list.insert(seg_word_index + 1, removed_gloss_split[2])

                        # Update the current word and its position, for the sake of the while loop
                        seg_word = word_without_clitic
                        seg_word_index += 1

                    else:
                        possibly_more_pre_clitics = False
                else:
                    possibly_more_pre_clitics = False

            # Now that we've dealt with initial clitics, check for final clitics
            while possibly_more_post_clitics:
                # SINGLE ENCLITIC CHECK
                # Does the word end with a clitic from our list, connected with a '='?
                clitic_check = seg_word.rpartition(CLITIC_BOUNDARY) # rpartition starts from the end of the word
                # If there was an equals sign, and a clitic after it
                potential_clitic_original_form = clitic_check[2]
                potential_clitic = re.sub(PUNCTUATION_TO_IGNORE, "", potential_clitic_original_form)
                if clitic_check[1] != "" and potential_clitic in post_clitics.keys():
                    clitic = potential_clitic
                    clitic_original_form = potential_clitic_original_form
                    word_without_clitic = clitic_check[0]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    if _clitic_in_word_list(post_clitics[clitic], ortho_line_word_list) and word_without_clitic != "":
                        # Okay, now we need to modify the seg and gloss lines
                        assert len(seg_line_word_list) == len(gloss_line_word_list), f"Error: There are {len(seg_line_word_list)} words in the seg line, but {len(gloss_line_word_list)} words in the gloss line! \nSeg line word list: {seg_line_word_list}"

                        # Replace this word in the list with two words, separating the clitic
                        seg_line_word_list.pop(seg_word_index)
                        seg_line_word_list.insert(seg_word_index, word_without_clitic)
                        seg_line_word_list.insert(seg_word_index + 1, clitic_original_form)

                        # Split the gloss
                        removed_gloss_word = gloss_line_word_list.pop(seg_word_index)
                        removed_gloss_split = removed_gloss_word.rpartition(CLITIC_BOUNDARY)
                        gloss_line_word_list.insert(seg_word_index, removed_gloss_split[0])
                        gloss_line_word_list.insert(seg_word_index + 1, removed_gloss_split[2])

                        # Update the current word, for the sake of the while loop
                        seg_word = word_without_clitic

                    else:
                        possibly_more_post_clitics = False
                else:
                    possibly_more_post_clitics = False

                # DOUBLE ENCLITIC CHECK
                # Now let's check for double post clitics - literally done for THREE examples... oh well
                # I've fully separated this from the regular post clitic check because they don't need to
                # interact at this point, and it's simpler this way
                clitic_check = seg_word.rpartition(CLITIC_BOUNDARY)
                second_clitic = clitic_check[2]
                clitic_check = clitic_check[0].rpartition(CLITIC_BOUNDARY)
                first_clitic = clitic_check[2]
                potential_double_clitic_original_form = first_clitic + CLITIC_BOUNDARY + second_clitic
                potential_double_clitic = re.sub(PUNCTUATION_TO_IGNORE, "", potential_double_clitic_original_form)
                # Does this segmented word end in a double clitic?
                if clitic_check[1] != "" and potential_double_clitic in double_post_clitics.keys():
                    clitic = potential_double_clitic
                    clitic_original_form = potential_double_clitic_original_form
                    word_without_clitic = clitic_check[0]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    if _clitic_in_word_list(double_post_clitics[clitic], ortho_line_word_list) and word_without_clitic != "":
                        assert len(seg_line_word_list) == len(gloss_line_word_list), f"Error: There are {len(seg_line_word_list)} words in the seg line, but {len(gloss_line_word_list)} words in the gloss line! \nSeg line word list: {seg_line_word_list}"

                        # Replace this word in the list with two words, separating the clitic
                        seg_line_word_list.pop(seg_word_index)
                        seg_line_word_list.insert(seg_word_index, word_without_clitic)
                        seg_line_word_list.insert(seg_word_index + 1, clitic_original_form)

                        # Split the gloss
                        removed_gloss_word = gloss_line_word_list.pop(seg_word_index)
                        removed_gloss_split = removed_gloss_word.rpartition(CLITIC_BOUNDARY)
                        second_clitic_gloss = removed_gloss_split[2]
                        removed_gloss_split = removed_gloss_split[0].rpartition(CLITIC_BOUNDARY)
                        first_clitic_gloss = removed_gloss_split[2]
                        # Stuff before the double clitic
                        gloss_line_word_list.insert(seg_word_index, removed_gloss_split[0])
                        # The double clitic
                        gloss_line_word_list.insert(seg_word_index + 1, first_clitic_gloss + CLITIC_BOUNDARY + second_clitic_gloss)

                        # Update the current word, for the sake of the while loop
                        # (We're already at the end of the loop here, but for consistency)
                        seg_word = word_without_clitic

        # Reassemble the modified lines
        seg_line = " ".join(seg_line_word_list)
        gloss_line = " ".join(gloss_line_word_list)
        updated_data.append([ortho_line, seg_line, gloss_line, example[3]])

    return updated_data

# Compare without worrying about accents, because stress can be inconsistenly marked between orthog/seg
def _same_clitic(clitic_1, clitic_2):
    clitic_1 = re.sub("á", "a", clitic_1)
    clitic_2 = re.sub("á", "a", clitic_2)
    clitic_1 = re.sub("ú", "u", clitic_1)
    clitic_2 = re.sub("ú", "u", clitic_2)

    return clitic_1 == clitic_2

def _clitic_in_word_list(clitic, word_list):
    found = False
    for word in word_list:
        if _same_clitic(clitic, word):
            found = True

    return found

def mark_OOL_words(data, OOL_WORDS, LINES_PER_SENTENCE):
    for example in data:
        # Only consider full examples
        if len(example) == LINES_PER_SENTENCE:
            transcription_words = example[0].split()
            seg_words = example[1].split()
            gloss_words = example[2].split()
                # Go word-by-word through the sentence
            for word_index, (transciption_word, seg_word, gloss_word) in enumerate(zip(transcription_words, seg_words, gloss_words)):
                # Check for any of the target words
                if transciption_word in OOL_WORDS:
                    word = transciption_word
                    # Next check this word is identical in the seg and gloss lines, too
                    if seg_word == word and gloss_word == word:
                        # Mark the word in the transcription, segmentation, and gloss lines
                        transcription_words[word_index] = OUT_OF_LANGUAGE_MARKER + word
                        seg_words[word_index] = OUT_OF_LANGUAGE_MARKER + word
                        gloss_words[word_index] = OUT_OF_LANGUAGE_MARKER + word

            example[0] = " ".join(transcription_words)
            example[1] = " ".join(seg_words)
            example[2] = " ".join(gloss_words)
            for i in range(0, 3):
                # Prevent double OOL markers
                example[i] = re.sub(DOUBLE_OOL_MARKER_REGEX, OUT_OF_LANGUAGE_MARKER, example[i])

    return data

# Matches any words that are marked as OOL (e.g., "*Mary" OR "OOL")
# Can replace with "OOL" or just delete (does the latter by default)
def handle_OOL_words(datasets, replace = False):
    updated_datasets = []
    for dataset in datasets:
        updated_dataset = []
        for example in dataset:
            updated_example = []
            for line in example:
                words = line.split()
                updated_words = words.copy()
                word_number = 0
                # Go word-by-word, and remove any marked with an asterisk
                # We are looping with while because the number of words can *change* if we remove any!
                # If replace = True, replace the asterisked words with a generic label
                while word_number < len(updated_words):
                    word = updated_words[word_number]
                    if word.startswith(OUT_OF_LANGUAGE_MARKER) or word == OUT_OF_LANGUAGE_LABEL:
                        updated_words.pop(word_number)
                        if not replace:
                            word_number -= 1 # To cancel out the incrementation
                        else: # Replace!
                            updated_words.insert(word_number, OUT_OF_LANGUAGE_LABEL)
                    word_number += 1

                updated_line = " ".join(updated_words)
                updated_example.append(updated_line)
            updated_dataset.append(updated_example)
        updated_datasets.append(updated_dataset)

    return updated_datasets

# We have a list of predicted lines, each of which is a list of words
# Go through the input lines to know where to add back in OOL words, then convert the whole line to a string for printing
def add_back_OOL_words(transcription_lines, predicted_lines):
    updated_predicted_lines = []

    # But also, add back in words marked as OOL.
    for transcription_line, predicted_line in zip(transcription_lines, predicted_lines):
        updated_predicted_line = predicted_line
        # Add back any asterisk-marked words
        for index, input_word in enumerate(transcription_line.split()):
            if input_word.startswith(OUT_OF_LANGUAGE_MARKER):
                updated_predicted_line.insert(index, input_word)

        # Remove any instances of the OOL label, if used
        while OUT_OF_LANGUAGE_LABEL in updated_predicted_line:
            OOL_pos = updated_predicted_line.index(OUT_OF_LANGUAGE_LABEL)
            updated_predicted_line.pop(OOL_pos)

        updated_predicted_line = " ".join(updated_predicted_line)
        # Update our progress through the predicted word list
        updated_predicted_lines.append(updated_predicted_line)

    return updated_predicted_lines

def create_file_of_sentences(examples, file_name, directory_path, randomize_order = False):
    # Create the generated_data subdirectory, if it doesn't already exist
    if not path.exists(directory_path):
        mkdir(directory_path)

    write_sentences(examples, directory_path + file_name, randomize_order)

# Assumes that lines do NOT end in "\n", and will add it as it prints
def write_sentences(examples, file_path, randomize_order = False):
    examples_to_write = examples
    if randomize_order:
        shuffle(examples_to_write)

    with open(file_path, "w") as file:
        for i, example in enumerate(examples_to_write):
            if len(example) > 0:
                for j, line in enumerate(example):
                    file.write(line + "\n")
                    # Add blank line after each example (but not if it's the end of the dataset, bc that results in a double newline at EOF)
                    if (j >= len(example) - 1) and (i < len(examples_to_write) - 1):
                        file.write("\n")
        file.close()

# Problem: a word has stress marked in one of the transcription or segmented lines, but not the other
# Sol'n: add stress in the right spot to the word in the other line!
def fix_inconsistent_stress(examples, maintain_NFC_unicode = False):
    updated_examples = []

    for example in examples:
        updated_example = example

        # Only look at proper 4-line glossed lines
        if len(example) == NUMBER_OF_LINES:

            # Convert to split chars/diacritics so we don't have to handle both input styles
            transcription_line = normalize('NFD', example[0])
            seg_line = normalize('NFD', example[1])

            BOUNDARIES_OR_SPACE_REGEX = "-|=|~|·|<|>| "
            seg_morphemes = re.split(BOUNDARIES_OR_SPACE_REGEX, seg_line)
            transcription_line_unstressed = transcription_line.replace(UNICODE_STRESS, "")
            seg_line_unstressed = seg_line.replace(UNICODE_STRESS, "")

            for i, morpheme in enumerate(seg_morphemes):
                # Check for stress in the seg line that's missing in the transcription line
                if UNICODE_STRESS in morpheme:
                    morpheme_unstressed = morpheme.replace(UNICODE_STRESS, "")
                    # If we're missing the corresponding stress in the transcription line...
                    if (transcription_line.count(morpheme) < seg_line.count(morpheme)) and (morpheme_unstressed in transcription_line):
                        # ...then add the stress to the transcription line!
                        if transcription_line.count(morpheme_unstressed) == 1: # Easy case -- only one possible target for changing
                            transcription_line = transcription_line.replace(morpheme_unstressed, morpheme, 1)
                        elif transcription_line_unstressed.count(morpheme_unstressed) == seg_line_unstressed.count(morpheme_unstressed): # Slightly more complex case
                            # This is the xth instance of this morpheme in the seg line. Solve for x.
                            prev_seg_line_unstressed = (" ".join(seg_morphemes[:i])).replace(UNICODE_STRESS, "")
                            instances_to_skip = prev_seg_line_unstressed.count(morpheme_unstressed)
                            starting_point = 0
                            for j in range(instances_to_skip): # Should never run if x = 0
                                next_unstressed_instance_pos = transcription_line.find(morpheme_unstressed, starting_point)
                                next_stressed_instance_pos = transcription_line.find(morpheme, starting_point)
                                assert((next_unstressed_instance_pos != -1) or (next_stressed_instance_pos != -1)) # at least one instance was found
                                if next_unstressed_instance_pos == -1:
                                    starting_point = next_stressed_instance_pos + len(morpheme)
                                elif next_stressed_instance_pos == -1:
                                    starting_point = next_unstressed_instance_pos + len(morpheme_unstressed)
                                # Both have values
                                elif next_stressed_instance_pos < next_unstressed_instance_pos:
                                    starting_point = next_stressed_instance_pos + len(morpheme)
                                else:
                                    starting_point = next_unstressed_instance_pos + len(morpheme_unstressed)

                            morpheme_pos = transcription_line.find(morpheme_unstressed, starting_point)
                            assert(morpheme_pos != -1)
                            transcription_line = transcription_line[:morpheme_pos] + morpheme + transcription_line[morpheme_pos + len(morpheme_unstressed):]

                # Check for stress in the transcription line that's missing in the seg line
                else:
                    # Regex b/c if you search for "example", you will get a match from "examplé" because the diacritic is considered the following character
                    # Okay this line is kind of cursed but the sub() are just to temporarily replace [] with \[\] to prevent them from being interpreted as regex argh
                    morpheme_is_in_transcription_line = re.search((re.sub(r"(\[|\])", r"\\\1", morpheme)) + "[^" + UNICODE_STRESS + "]*", re.sub(r"(\[|\])", r"\\\1", transcription_line))
                    # If we're missing the corresponding stress in the seg line...
                    # (The last condition here is ridiculous but necessary to not over-fix in some erroenous data).
                    if (not (morpheme_is_in_transcription_line)) and (morpheme in transcription_line_unstressed) and (transcription_line_unstressed.count(morpheme) >= seg_line_unstressed.count(morpheme)):
                        if seg_line.count(morpheme) == 1: # Don't do anything if there's multiple possible targets.
                            # Find the stressed version of the morpheme in the transcription line
                            for transcription_word in transcription_line.split():
                                if len(transcription_word) >= len(morpheme) + 1: # +1 because stress adds a char
                                    for starting_index in range(len(transcription_word) - (len(morpheme))):
                                        possible_morpheme = transcription_word[starting_index : (starting_index + len(morpheme) + 1)]
                                        if possible_morpheme.replace(UNICODE_STRESS, "") == morpheme:
                                            # ...then add the stress to the seg line!
                                            seg_line = seg_line.replace(morpheme, possible_morpheme)
                                            seg_morphemes[i] == possible_morpheme # To keep this loop updated

            if maintain_NFC_unicode:
                transcription_line = normalize('NFC', transcription_line)
                seg_line = normalize('NFC', seg_line)
            updated_example = [transcription_line, seg_line, example[2], example[3]]

        updated_examples.append(updated_example)

    return updated_examples
