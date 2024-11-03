# *** Common functions for working with glossed data ***
import re

REGULAR_BOUNDARY = "-"
CLITIC_BOUNDARY = "="
REDUPLICATION_BOUNDARY = "~"
LEFT_INFIX_BOUNDARY = "<"
RIGHT_INFIX_BOUNDARY = ">"
LEFT_REDUP_INFIX_BOUNDARY = "{"
RIGHT_REDUP_INFIX_BOUNDARY = "}"
NON_INFIXING_BOUNDARIES = [REGULAR_BOUNDARY, REDUPLICATION_BOUNDARY, CLITIC_BOUNDARY]

# Removes the brackets but *leaves* the bracketed affix in.
def ignore_brackets(sentence):
    sentence = re.sub(r'[\[\]]', "", sentence)
    return sentence 

# Given a segmentation line, return a list of its morphemes
# The keep_word_boundaries parameter specfies whether you want the returned morpheme list
# to be divided into word sub-lists
# For example:
# keep_word_boundaries = False, then it returns [w1m1, w1m2, w2m1, w2m2]
# keep_word_boundaries = True, then it returns [[w1m1, w1m2], [w2m1, w2m2]]
def seg_line_to_morphemes(seg_line, do_ignore_brackets, keep_word_boundaries = False):
    morpheme_list = []
    if keep_word_boundaries:
        word_list = []

    if do_ignore_brackets:
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

        if keep_word_boundaries and morpheme_list: # Only if non-empty (again, to avoid empty morphemes)
            word_list.append(morpheme_list)
            morpheme_list = []

    if keep_word_boundaries:
        return word_list
    else:
        return morpheme_list

# Returns a list of glosses (one for each morpheme in the sentence)
# This won't modify the input parameter btw ha ha
def gloss_line_to_morphemes(gloss_line, keep_word_boundaries = False):
    gloss_line = ignore_brackets(gloss_line)
    # Recall that infix boundaries aren't so complex to handle in the gloss line (just gloss1<gloss2>-gloss3)
    # We can just replace them with regular boundaries here, so they'll get handled by the re.split line
    gloss_line = re.sub(r"[" + LEFT_INFIX_BOUNDARY + "\\" + LEFT_REDUP_INFIX_BOUNDARY + "]", REGULAR_BOUNDARY, gloss_line)
    gloss_line = re.sub(r"[" + RIGHT_INFIX_BOUNDARY + "\\" + RIGHT_REDUP_INFIX_BOUNDARY + "]", "", gloss_line)

    # Break apart line morpheme-by-morpheme
    if keep_word_boundaries: # Maintain word-level sub-lists of morphemes
        gloss_line = gloss_line.split()
        updated_gloss_line = []
        for word in gloss_line:
            word = re.split(r"[" + re.escape("".join(NON_INFIXING_BOUNDARIES)) + r"]", word)
            updated_gloss_line.append(word)
        gloss_line = updated_gloss_line
    else: # Just split the line into a list of morphemes, with no word structure maintained
        gloss_line = re.split(r"[" + re.escape("".join(NON_INFIXING_BOUNDARIES)) + "\s" + r"]", gloss_line)

    return gloss_line
