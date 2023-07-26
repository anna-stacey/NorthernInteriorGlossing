# Goal: seg line has <> for non-reduplicating infixes, ~ for non-infxing reduplication, {} for infixing reduplication, and - for all else
# St̓át̓imcets data currently has ~ for infixes, - for all else
# In order to detect redup, we will need to identify the corresponding gloss
import click
import re
from Data.statimcets.annotate import read_file, create_file

# Segmentation boundaries
PREV_INFIX_BOUNDARY = "~"
LEFT_INFIX_BOUNDARY = "<"
RIGHT_INFIX_BOUNDARY = ">"
LEFT_INFIX_REDUP_BOUNDARY = "{"
RIGHT_INFIX_REDUP_BOUNDARY = "}"
REDUP_BOUNDARY = "~"
REGULAR_BOUNDARY = "-"

# Gloss boundaries
GLOSS_BOUNDARY = "-"

# Counting where the first line = 1
SEG_LINE_NUMBER = 2
GLOSS_LINE_NUMBER = 3
INFIXING_REDUPLICANT = "CRED"
# TRED·, IRED· and ·FRED
PRE_REDUP = ["TRED", "IRED"]
POST_REDUP = ["FRED"]
NON_INFIXING_REDUPLICANTS = PRE_REDUP + POST_REDUP


def handle_infix(seg_word, left_marker, right_marker):
    seg_word = re.sub(PREV_INFIX_BOUNDARY, left_marker, seg_word, 1)
    seg_word = re.sub(PREV_INFIX_BOUNDARY, right_marker, seg_word, 1)

    return seg_word

def identify_type_of_infixing(seg_word, gloss_word):
    assert seg_word.count(PREV_INFIX_BOUNDARY) == 2, seg_word
    # Identify infixing reduplication
    if INFIXING_REDUPLICANT in gloss_word.split(REGULAR_BOUNDARY):
        seg_word = handle_infix(seg_word, LEFT_INFIX_REDUP_BOUNDARY, RIGHT_INFIX_REDUP_BOUNDARY)
    # Otherwise it's an infix but not reduplication
    else:
        seg_word = handle_infix(seg_word, LEFT_INFIX_BOUNDARY, RIGHT_INFIX_BOUNDARY)
    
    return seg_word

# Note that reduplication direction can vary i.e. TRED· vs ·FRED
# Determine the location of the reduplicated morpheme, and mark it with unique boundaries
def handle_other_redup(seg_word, gloss_word):
    seg_morphemes = seg_word.split(REGULAR_BOUNDARY) # Can ignore infixes
    gloss_morphemes = gloss_word.split(GLOSS_BOUNDARY)

    new_seg_word = []
    # Go morpheme by morpheme, and add each morpheme plus the following boundary
    for seg_morpheme, gloss_morpheme in zip(seg_morphemes, gloss_morphemes):
        # reduplicant ~ rest of word
        if gloss_morpheme in PRE_REDUP:
            new_seg_word.append(seg_morpheme)
            new_seg_word.append(REDUP_BOUNDARY)
        # rest of word ~ reduplicant
        elif gloss_morpheme in POST_REDUP:
            # Remove the previous boundary and replace it
            new_seg_word.pop(len(new_seg_word) - 1)
            new_seg_word.append(REDUP_BOUNDARY)
            new_seg_word.append(seg_morpheme)
            new_seg_word.append(REGULAR_BOUNDARY)
        # Not reduplication, just a regular morpheme
        else:
            new_seg_word.append(seg_morpheme)
            new_seg_word.append(REGULAR_BOUNDARY)
    
    # The last boundary is unnecessary and should be removed
    new_seg_word.pop(len(new_seg_word) - 1)

    return "".join(new_seg_word)

def process_data(data):
    new_data = []

    # Note that only the seg line is being edited
    for example in data:
        new_example = []
        new_seg_line = []
        seg_line = example[SEG_LINE_NUMBER - 1]
        gloss_line = example[GLOSS_LINE_NUMBER - 1]
        for seg_word, gloss_word in zip(seg_line.split(" "), gloss_line.split(" ")):
            # Check for infixes
            if PREV_INFIX_BOUNDARY in seg_word:
                seg_word = identify_type_of_infixing(seg_word, gloss_word)
            # Check for non-infixing reduplication
            if any(reduplicant in gloss_word for reduplicant in NON_INFIXING_REDUPLICANTS):
                seg_word = handle_other_redup(seg_word, gloss_word)

            new_seg_line.append(seg_word)

        new_example = [example[0], " ".join(new_seg_line), example[2], example[3]]       
        new_data.append(new_example)

    return new_data

def split_into_stories(data):
    # There are 18 stories of varying length
    story_lengths = [114, 53, 24, 73, 59, 25, 52, 32, 46, 67, 37, 66, 30, 16, 74, 79, 47, 83]
    example_index = 0
    for i, story_length in enumerate(story_lengths):
        create_file(data[example_index:example_index + story_length], f"story_{i + 1}.txt")
        example_index += story_length

@click.command()
@click.option("--input_file", help = "The name of the file containing all sentences.")
@click.option("--output_file", help = "The name of the file where the modified sentences will be written to.")
def main(input_file, output_file):
    data = read_file(input_file)
    data = process_data(data)
    create_file(data, output_file)
    split_into_stories(data)

main()
# python3 src/boundaries.py --input_file=./data/statimcets/statimcets_data_annotated.txt --output_file=statimcets_data_double_annotated.txt
