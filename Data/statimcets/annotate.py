import re

# Returns a list of examples (where each example is a list containing the 5 lines)
def read_file(file_path):
    with open(file_path) as f:
        lines = f.readlines()

    sentences = []
    current_sentence = []
    for i, line in enumerate(lines):
        if (i + 1) % 5 == 0: # Every 5th line is a blank line marking the end of the current sentence
            sentences.append(current_sentence)
            current_sentence = []
        else:
            current_sentence.append(line)
    return(sentences)

# Given a list of examples, print each line with a blank line in between examples
def create_file(list, file_name):
    file = open(file_name, "w")
    for example in list:
        for line in example:
            file.write(line)
        file.write("\n")
    file.close()

# We want to make only minimal changes to the source line
def preprocess_source(line):
    # Just remove double quotes
    line = re.sub("''", "", line)
    line = re.sub("``", "", line)
    return line

# Changes specific to the seg line
def preprocess_seg(line):
    # Brackets surround stuff in the seg line
    # If this 'stuff' did not appear in the orthography line, I manually removed it
    # If it did appear, then we just want to remove the brackets themselves, but leave in their contents
    line = re.sub("\[", "", line)
    line = re.sub("\]", "", line)

    return line

# Changes specific to the gloss line
def preprocess_gloss(line):
    # In the gloss line, brackets were just used a few times - not sure why
    # It was stuff like [INVIS]
    # For now these are being removed, though should perhaps consider just changing to using a period
    line = re.sub("\[[^\]]*\]", "", line)
    return line


# Changes common to seg and gloss lines
def preprocess(line):
    # " only appears once, in an overall anomalous example, which has been removed (see EOF)

    # Once in the seg line, there are quotes which need a space in between
    line = re.sub("''``", "'' ``", line)

    # '' is used for the end of quotations, in the source, segmented and translation lines
    # it is sometimes asymmetric i.e. has no corresponding opening quotations marks (possibly only at the start of source lines, but it occurs often)
    # Sometimes this lines up between source and segmented line, sometimes it doesn't
    line = re.sub("''", "", line)

    # `` is used to open quotations in the source, seg, and translation lines
    # It seems to be omitted if it would be at the very beginning of a source line (but still shows up in the corresponding seg/trs lines)
    line = re.sub("``", "", line)

    # Ellipses are used for hesitations
    line = re.sub("\.\.\.", "", line)

    # Single ' is used to indicate something orthographically (generally ejectives I believe).

    # Parentheses typically surround things that are not phonologically realized
    # When these were whole morphemes, I removed them manually from the seg/gloss lines (see EOF)
    # There are ~10 instances where the parenthetic content was just part of a morpheme, and so can be removed
    # here for the sake of matching the orthography line, with no effect on any alignment
    # There is also one use of parentheses in the gloss line (VIS), which can be removed in the same way
    # that we are removing the few instances of bracketed stuff from the gloss line
    line = re.sub("\([^\)]*\)", "", line)

    # : is used as punctuation (i.e. before a quote) in the src, seg, and trs lines
    # Leaving this in, along with other punctuation such as . and ,

    # :: seems to be something orthographical? So it's left in.
    # Used in the src and seg lines (14 times)

    # There are sometimes plus signs (with spaces on either side) in the seg line, relating to line breaks.
    # Removing these prevents them from being counted as an extra morpheme.
    line = re.sub("\s\+\s", " ", line)

    return line

def create_clitic_dicts():
    pre_clitic_keys = ["i", "ki", "ken", "ku", "kw", "kwa", "kwelh", "lhel", "na", "nelh", "ni", "ta", "ti", "wa7", "wi"]
    double_pre_clitics_keys = ["e=ta", "e=ki", "ken=ki", "ken=ku", "ken=ta", "l=ki", "l=na", "l=ta", "lhel=ki", "lhel=ku", "lhel=ta"] # Just for reference
    post_clitic_keys = ["cwílh", "hém'", "hem'", "iz'", "ká", "ka", "k'á", "k'a", "ku7", "kélh", "kelh", "klh", "malh", "ni7", "t'elh", "t'lh", "t'ú7", "t'u7", "ti7", "ts7a", "tú7", "tu7", "wi", "wi7"]
    double_post_clitic_keys = ["tú7=a", "t'ú7=a"]
    pre_clitics = {}
    for pre_clitic_key in pre_clitic_keys:
        pre_clitics.update({pre_clitic_key: pre_clitic_key})
    #pre_clitics.update({"wá7": "wa7"})

    double_pre_clitics = {}
    double_pre_clitics.update({"e=ta": "éta"})
    double_pre_clitics.update({"e=ki": "éki"})
    double_pre_clitics.update({"ken=ki": "kénki"})
    double_pre_clitics.update({"ken=ku": "kenkú"}) # Only one instance
    double_pre_clitics.update({"ken=ta": "kénta"})
    double_pre_clitics.update({"l=ki": "lki"})
    double_pre_clitics.update({"l=kwa": "lkwa"}) # Only one instance
    double_pre_clitics.update({"l=na": "lna"}) # Only one instance
    double_pre_clitics.update({"l=ta": "lta"})
    double_pre_clitics.update({"lhel=ki": "lhélki"})
    double_pre_clitics.update({"lhel=ku": "lhelkú"})
    double_pre_clitics.update({"lhel=ta": "lhélta"})

    post_clitics = {}
    for post_clitic_key in post_clitic_keys:
        post_clitics.update({post_clitic_key: post_clitic_key})
    post_clitics.update({"klh": "kelh"})
    post_clitics.update({"t'lh": "t'elh"})

    double_post_clitics = {}
    double_pre_clitics.update({"tú7=a": "tú7a"}) # Only one instance
    double_pre_clitics.update({"t'ú7=a": "t'ú7a"})

    return pre_clitics, double_pre_clitics, post_clitics, double_pre_clitics

# Compare without worrying about accents, because stress can be inconsistenly marked between orthog/seg
def same_clitic(clitic_1, clitic_2):
    clitic_1 = re.sub("á", "a", clitic_1)
    clitic_2 = re.sub("á", "a", clitic_2)
    clitic_1 = re.sub("ú", "u", clitic_1)
    clitic_2 = re.sub("ú", "u", clitic_2)

    return clitic_1 == clitic_2

def clitic_in_word_list(clitic, word_list):
    found = False
    for word in word_list:
        if same_clitic(clitic, word):
            found = True
    
    return found

# Fix the issue of clitics which are standalone in the orthographic line, but attached to a larger word in the segmentation and gloss lines
# Solution: Make it standalone in the seg and gloss lines too (to prevent altering the orthographic line)
def handle_clitics(data):
    misalignment_count = 0
    updated_data = []
    pre_clitics, double_pre_clitics, post_clitics, double_post_clitics = create_clitic_dicts()
    for example in data:
        ortho_line = example[0]
        seg_line = example[1]
        gloss_line = example[2]
        # Grab all the words in the orthography line, so we can look for clitics as words there
        # Remove punctuation so it doesn't get in the way of looking for the particular clitic
        ortho_line_word_list = (re.sub("\.|,|\?|!|:", "", ortho_line)).split()
        seg_line_word_list = seg_line.split()
        gloss_line_word_list = gloss_line.split()
        for i, word in enumerate(seg_line_word_list):
            possibly_more_pre_clitics = True
            possibly_more_post_clitics = True
            while possibly_more_pre_clitics:
                # Does the word start with a clitic from our list, connected with a '='?
                clitic_check = word.partition("=")
                # If there was an equals sign, and a clitic before it
                if clitic_check[1] != "" and clitic_check[0] in pre_clitics.keys():
                    #print(word)
                    clitic = clitic_check[0]
                    #clitic = re.sub("\.", "", clitic)
                    word_without_clitic = clitic_check[2]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    # This check is quite strict -
                    # It will prevent problems with the wrong word being looked at, but it's also going to (at present)
                    # exclude a lot of problematic lines from being fixed. Something to think about...
                    if len(ortho_line_word_list) > i and ortho_line_word_list[i].lower() == pre_clitics[clitic]:
                        #print(ortho_line_word_list[i])
                        # Okay, now we need to modify the seg and gloss lines
                        # The below should always be true, so eventually this should just be a sanity check (and could be an assert)
                        if len(seg_line_word_list) == len(gloss_line_word_list):

                            # Replace this word in the list with two words, separating the clitic
                            seg_line_word_list.pop(i)
                            seg_line_word_list.insert(i, clitic)
                            seg_line_word_list.insert(i + 1, word_without_clitic)

                            # Split the gloss
                            removed_gloss_word = gloss_line_word_list.pop(i)
                            removed_gloss_split = removed_gloss_word.partition("=")
                            gloss_line_word_list.insert(i, removed_gloss_split[0])
                            gloss_line_word_list.insert(i + 1, removed_gloss_split[2])

                            # Update the current word and its position, for the sake of the while loop
                            word = word_without_clitic
                            i += 1
                        else:
                            possibly_more_pre_clitics = False
                    else:
                        possibly_more_pre_clitics = False
                # Repeat, but this time for the double clitics
                double_clitic_check = clitic_check[2].partition("=")
                # Reassemble, around this SECOND equals sign
                clitic_check = (clitic_check[0] + "=" + double_clitic_check[0], "=", double_clitic_check[2])
                if clitic_check[1] != "" and clitic_check[0] in double_pre_clitics.keys():
                    clitic = clitic_check[0]
                    word_without_clitic = clitic_check[2]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    # This check is quite strict -
                    # It will prevent problems with the wrong word being looked at, but it's also going to (at present)
                    # exclude a lot of problematic lines from being fixed. Something to think about...
                    if len(ortho_line_word_list) > i and ortho_line_word_list[i] == double_pre_clitics[clitic]:
                        # Okay, now we need to modify the seg and gloss lines
                        # The below should always be true, so eventually this should just be a sanity check (and could be an assert)
                        if len(seg_line_word_list) == len(gloss_line_word_list):

                            # Replace this word in the list with two words, separating the clitic
                            seg_line_word_list.pop(i)
                            seg_line_word_list.insert(i, clitic)
                            seg_line_word_list.insert(i + 1, word_without_clitic)

                            # Split the gloss
                            removed_gloss_word = gloss_line_word_list.pop(i)
                            removed_gloss_split = removed_gloss_word.partition("=")
                            double_removed_gloss_split = removed_gloss_split[2].partition("=")
                            removed_gloss_split = (removed_gloss_split[0] + "=" + double_removed_gloss_split[0], "=", double_removed_gloss_split[2])
                            gloss_line_word_list.insert(i, removed_gloss_split[0])
                            gloss_line_word_list.insert(i + 1, removed_gloss_split[2])

                            # Update the current word, for the sake of the while loop
                            word = word_without_clitic

                        else:
                            possibly_more_pre_clitics = False
                    else:
                        possibly_more_pre_clitics = False
                else:
                    possibly_more_pre_clitics = False

            # Now that we've dealt with initial clitics, check for final clitics
            while possibly_more_post_clitics:
                # Does the word end with a clitic from our list, connected with a '='?
                clitic_check = word.rpartition("=") # rpartition starts from the end of the word
                # If there was an equals sign, and a clitic after it
                potential_clitic_original_form = clitic_check[2]
                potential_clitic = re.sub("\.|,|\?|!|:", "", potential_clitic_original_form)
                if clitic_check[1] != "" and potential_clitic in post_clitics.keys():
                    clitic = potential_clitic
                    clitic_original_form = potential_clitic_original_form
                    word_without_clitic = clitic_check[0]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    if clitic_in_word_list(post_clitics[clitic], ortho_line_word_list):
                        # Okay, now we need to modify the seg and gloss lines
                        # The below should always be true, so eventually this should just be a sanity check (and could be an assert)
                        if len(seg_line_word_list) == len(gloss_line_word_list):

                            # Replace this word in the list with two words, separating the clitic
                            seg_line_word_list.pop(i)
                            seg_line_word_list.insert(i, word_without_clitic)
                            seg_line_word_list.insert(i + 1, clitic_original_form)

                            # Split the gloss
                            removed_gloss_word = gloss_line_word_list.pop(i)
                            removed_gloss_split = removed_gloss_word.rpartition("=")
                            gloss_line_word_list.insert(i, removed_gloss_split[0])
                            gloss_line_word_list.insert(i + 1, removed_gloss_split[2])

                            # Update the current word, for the sake of the while loop
                            word = word_without_clitic

                        else:
                            possibly_more_post_clitics = False
                    else:
                        possibly_more_post_clitics = False
                else:
                    possibly_more_post_clitics = False

                # Now let's check for double post clitics - literally done for THREE examples... oh well
                # I've fully separated this from the regular post clitic check because they don't need to
                # interact at this point, and it's simpler this way
                clitic_check = word.rpartition("=")
                second_clitic = clitic_check[2]
                clitic_check = clitic_check[0].rpartition("=")
                first_clitic = clitic_check[2]
                potential_double_clitic_original_form = first_clitic + "=" + second_clitic
                potential_double_clitic = re.sub("\.|,|\?|!|:", "", potential_double_clitic_original_form)
                # Does this segmented word end in a double clitic?
                if clitic_check[1] != "" and potential_double_clitic in double_post_clitics.keys():
                    clitic = potential_double_clitic
                    clitic_original_form = potential_double_clitic_original_form
                    word_without_clitic = clitic_check[0]
                    # Now: does that clitic appear as its own word in the orthographic line?
                    if clitic_in_word_list(double_post_clitics[clitic], ortho_line_word_list):
                            
                            # Replace this word in the list with two words, separating the clitic
                            seg_line_word_list.pop(i)
                            seg_line_word_list.insert(i, word_without_clitic)
                            seg_line_word_list.insert(i + 1, clitic_original_form)

                            # Split the gloss
                            removed_gloss_word = gloss_line_word_list.pop(i)
                            removed_gloss_split = removed_gloss_word.rpartition("=")
                            second_clitic_gloss = removed_gloss_split[2]
                            removed_gloss_split = removed_gloss_split[0].rpartition("=")
                            first_clitic_gloss = removed_gloss_split[2]
                            # Stuff before the double clitic
                            gloss_line_word_list.insert(i, removed_gloss_split[0])
                            #The double clitic
                            gloss_line_word_list.insert(i + 1, first_clitic_gloss + "=" + second_clitic_gloss)

                            # Update the current word, for the sake of the while loop
                            # (We're already at the end of the loop here, but for consistency)
                            word = word_without_clitic

        # Reassemble the modified lines
        seg_line_word_list.append("\n")
        seg_line = " ".join(seg_line_word_list)
        gloss_line_word_list.append("\n")
        gloss_line = " ".join(gloss_line_word_list)
        updated_data.append([ortho_line, seg_line, gloss_line, example[3]])
    
    print(f"Misalignment count: {misalignment_count}")
    return updated_data

def general_annotate(data):
    new_data = []
    for example in data:
        new_example = []
        for i, line in enumerate(example):
            if i == 0: # The source/orthography line
                new_line = preprocess_source(line)
            elif i == 1: # The seg line
                new_line = preprocess(line)
                new_line = preprocess_seg(new_line)
            elif i == 2: # The gloss line
                new_line = preprocess(line)
                new_line = preprocess_gloss(new_line)
            else: # We don't need to modify the translation line
                new_line = line
            new_example.append(new_line)
        new_data.append(new_example)
    
    return new_data

# Convert infixing reduplication to have infix boundaries (<>)
# Convert reduplication that attaches as a refular affox to have regular boundaries (-)
def handle_reduplication(data):
    updated_data = []
    for example in data:
        seg_line = example[1]
        seg_list = seg_line.split()
        gloss_line = example[2]
        gloss_list = gloss_line.split()
        for i, word in enumerate(seg_list):
            # Some kind of reduplication
            if re.search("·", word):
                updated_word = word
                # There are a handful of examples with both CRED and another kind of reduplication
                # Let's convert the non-CRED boundary first, so that the changes for CRED don't get mixed up
                if word.count("·") == 3:
                    word_glossed = gloss_list[i]
                    # Does CRED occur before or after the other kind of reduplication?
                    cred_pos = word_glossed.find("CRED")
                    assert re.search("[^C]RED", word_glossed)
                    other_pos = (re.search("[^C]RED", word_glossed)).span()[0]
                    if (other_pos < cred_pos):
                        # Replace the first dot only
                        updated_word = updated_word.replace("·", "-", 1)
                    else:
                        # Replace the last dot only
                        dot_pos = updated_word.rfind("·")
                        updated_word = updated_word[:dot_pos] + "-'" + updated_word[(dot_pos + 1):]

                # Check if we're dealing with infixing reduplication
                if re.search("CRED", gloss_list[i]):
                    # Treat this reduplciation as an infix
                    updated_word = updated_word.replace("·", "<", 1)
                    updated_word = updated_word.replace("·", ">", 1)

                # For other kinds of reduplication, just replace the dots with hyphens
                updated_word = updated_word.replace("·", "-")
                # Update the seg line
                seg_list.pop(i)
                seg_list.insert(i, updated_word)
        
        updated_seg_line = " ".join(seg_list)
        updated_example = [example[0], updated_seg_line, gloss_line, example[3]]
        updated_data.append(updated_example)

    return updated_data

def handle_morpheme_boundaries(data):
    updated_data = []
    for example in data:
        seg_line = example[1]
        gloss_line = example[2]

        seg_line = re.sub("<|>", "~", seg_line)
        seg_line = re.sub("=", "-", seg_line)
        seg_line = re.sub("-\n", "\n", seg_line)

        gloss_line = re.sub("·|=|<|>", "-", gloss_line)
        gloss_line = re.sub("-+", "-", gloss_line) # Deals with double boundaries, e.g. ·=
        gloss_line = re.sub("- ", " ", gloss_line) # Deals with hanging boundaries, like light<INCH>
        gloss_line = re.sub(" -", " ", gloss_line) # Same as above - haven't seen this, but just to be safe

        updated_data.append([example[0], seg_line, gloss_line, example[3]])

    return updated_data

# How often does the number of words in the orthographic line not align with the number of words in the seg line?
def check_orthographic_misalignments(data):
    example_count = 0
    misalignment_count = 0
    for example in data:
        ortho_line = example[0]
        seg_line = example[1]
        if(len(ortho_line.split()) != len(seg_line.split())):
            misalignment_count += 1
            print(example[3])
        example_count += 1

    return misalignment_count

# Same as above, but removes probelmatic lines
def remove_orthographic_misalignments(data):
    new_data = []
    for example in data:
        ortho_line = example[0]
        seg_line = example[1]
        if(len(ortho_line.split()) == len(seg_line.split())):
            new_data.append(example)

    return new_data

def split_by_segmentation(line_with_segments):
    # The only morphemes boundaries we expect to see at this point are - and ~
    line_with_segments = re.sub("[\-~]", " ", line_with_segments)
    return line_with_segments.split()

def get_misaligned_data(data):
    misaligned_data = []
    example_count = 0
    mismatch_count = 0
    for example in data:
        if not seg_and_gloss_aligned(example):
            mismatch_count += 1
            misaligned_data.append(example)
        example_count += 1
    
    return mismatch_count, misaligned_data

# A reusable check that looks at a single example
def seg_and_gloss_aligned(example):
    aligned = True
    seg_line = example[1]
    gloss_line = example[2]
    seg_list = split_by_segmentation(seg_line)
    gloss_list = split_by_segmentation(gloss_line)
    seg_length = len(seg_list)
    gloss_length = len(gloss_list)

    infix_count = example[1].count("~")
    assert infix_count % 2 == 0
    seg_length -= (infix_count / 2)

    if (seg_length != gloss_length):
        aligned = False

    return aligned

# Remove lines where the seg/gloss lines are misaligned
def remove_gloss_misalignments(data):
    new_data = []
    for example in data:
        if(seg_and_gloss_aligned(example)):
            new_data.append(example)

    return new_data

def analyze_misalignments(misaligned_data):
    gloss_bracket_count = 0
    gloss_parentheses_count = 0
    gloss_cred_count = 0
    seg_plus_count = 0
    seg_bracket_count = 0
    seg_parentheses_count = 0
    seg_angle_bracket_count = 0
    for example in misaligned_data:
        for i, line in enumerate(example):
            if i == 1: # Segmentation line
                if re.search("\+", line):
                    print(example, "\n")
                    seg_plus_count += 1  
                if re.search("\[", line):
                    seg_bracket_count += 1
                if re.search("\(", line):
                    seg_parentheses_count += 1
                if re.search("<", line):
                    seg_angle_bracket_count += 1             
            if i == 2: # Gloss line
                if re.search("\[", line):
                    gloss_bracket_count += 1
                if re.search("CRED", line):
                    gloss_cred_count += 1
                if re.search("\(", line):
                    gloss_parentheses_count += 1

    print("Misaligned lines with plus signs in the seg line: ", seg_plus_count)
    print("Misaligned lines with brackets in the seg line: ", seg_bracket_count)
    print("Misaligned lines with parentheses in the seg line: ", seg_parentheses_count)
    print("Misaligned lines with angle brackets in the seg line: ", seg_angle_bracket_count)
    print("Misaligned lines with brackets in the gloss line: ", gloss_bracket_count)
    print("Misaligned lines with \"CRED\" in the gloss line: ", gloss_cred_count)
    print("Misaligned lines with parentheses in the gloss line: ", gloss_parentheses_count)
    #print("Overall number of misaligned lines: ", len(misaligned_data))

def main():
    ortho_seg_misalignment_count = -1
    seg_gloss_misalignment_count = -1
    data = read_file("statimcets-data.txt")
    example_count = len(data)

    data = general_annotate(data)
    data = handle_reduplication(data)
    data = handle_clitics(data)
    data = handle_morpheme_boundaries(data) # Move this to after the gloss checks to revert things lol

    ortho_seg_misalignment_count = check_orthographic_misalignments(data)
    #data = remove_orthographic_misalignments(data)

    seg_gloss_misalignment_count, misaligned_data = get_misaligned_data(data)
    #data = remove_gloss_misalignments(data)
    #analyze_misalignments(misaligned_data)

    #create_file(misaligned_data, "statimcets-data-misalignments.txt")
    create_file(data, "statimcets-data-annotated.txt")

    print(f"{ortho_seg_misalignment_count}/{example_count} examples are misaligned between orthography/seg.")
    print(f"{seg_gloss_misalignment_count}/{example_count - ortho_seg_misalignment_count} examples are incorrectly aligned between seg/gloss.")
    print(f"{example_count - ortho_seg_misalignment_count - seg_gloss_misalignment_count}/{example_count} examples are good to go.")
    assert (example_count - ortho_seg_misalignment_count - seg_gloss_misalignment_count) == len(data)

main()

# MANUAL CHANGES MADE:
# - removed comment from gloss line
        # Wá7lhkan kens7áz'en láti7 ta skúza7sa, cw7aoz kwas celhcálhtsas láti7 ta án'wasa squls ts'la7 stsáqwem.
        # ``wá7=lhkan kens-7áz'-en láti7 ta=skúza7-s=a''``cw7aoz kwas celh·cálh-ts-as láti7 ta=7án'was=a [s]-qul-s ts'la7 stsáqwem.''
        # %1sg.obj suffix elided from "celhcalhtsas"IPFV=FSGS want.to-buy-DIR at+there.VIS DET=offspring-TP=EXIS NEG DET+NMLZ+IPFV+TP TRED·willing+CAUS-FSGO-TE at+there.VIS DET=two=EXIS NMLZ-full-TP basket saskatoon.berry
        # ``I want to buy her daughter ``She won't let me have her for two baskets full of tsáqwem.''
# - removed single quotes (for quote within a quote) from source and segmented lines
        # Aoz,'' kan tsun, ``tsun `Náskan kelh.'
        # ``aoz,'' kan tsun, ``tsun, `nás=kan=kelh'.''
        # NEG FSGS say+DIR say+DIR go=FSGS=FUT
        # ``No,'' I told him, ``Tell him, `I will go'.''
# - removed English comment from source line
        # Nilh stsúntsalem láti7 sGí7i7 means `Magpie'. ta nsnuk'w7úla:
        # nilh s=tsún-tsalem láti7 s=Gí7i7 [ta]=n-snuk'w7-úl=a:
        # COP NMLZ=say+DIR-FSG.PASS at+there.VIS NMLZ=magpie DET=FSGP-relation-real=EXIS
        # Gí7i7 (Freddy), my cousin, told me:

        # Wá7lhkan tsun ta nstá7a: ``Cúz'lhkan nas t'útsslep' ku sp'ámsa.'' That would be, and another word would be wíwel'qem'.
        # wá7=lhkan tsun [ta]=n-stá7=a, ``cúz'=lhkan nas t'úts-slep' ku=sp'áms=a.''
        # IPFV=FSGS say+DIR DET=FSGP-aunt=EXIS going.to=FSGS go get.chopped-firewood DET=firewood=EXIS
        # I told my aunt, ``I'm going to go and chop some firewood.''
# - fixed misordered gloss line (corrected to match PDF)
        # Nilh hem' ti7 zam' aylh kaxéksasa ta nsqátsez7a, wa7 tsúnas láti7 t.snúk'wa7sa wa7 qwa7yán'ak, nilh t'u7 aylh lhus nq'san'kmínitas láti7, nilh t'u7 s7aylhts t'u7 ti7 aylh t'u7 skwátsitss, Qwa7yán'ak.
        # nílh=hem'=ti7 zam' aylh ka-xék-s-as-a ta=n-sqátsez7=a, wa7 tsún-as láti7 t=snúk'wa7-s=a wa7 ``qwa<7>y-án'ak'', nílh=t'u7 aylh lhus n-q's-an'k-mín-itas láti7 nílh=t'u7 s=7aylh=ts=t'ú7=ti7, áylh=t'u7 skwátsits-s, ``Qwa<7>y-án'ak''. 
        # COP=ANTI=that after.all then CIRC-reckon-CAUS-TE-CIRC DET=FSGP-father=EXIS COP=EXCL NMLZ=then=TP=EXCL=that then=EXCL name-TP blue<INCH>-stomach IPFV say+DIR-TE at+there.VIS DET=friend-TP=EXIS IPFV blue<INCH>-stomach COP=EXCL then COMP+IPFV+TC LOC-laugh-stomach-RLT-TPle at+there.VIS
        # My father figured that out when he told his friend he was qwa7yán'ak, and they laughed at him and then his name became Qwa7yán'ak after that.
# - moved +DIR, since it is a part of the word to which CRED applies (and get.found+DIR occurs many times elsewhere)
        # Púpen'lhkan láti7 i... 
        # pú·p·en'=lhkan láti7 i(n)...
        # get.found·CRED·+DIR=FSGS at+there.VIS PL.DET
        # I came across some...
# - changed gloss for "kan-em" from just do.what to do.what-MID, to match alignment and bc it appeared gloss this way 3x elsewhere
        # Iy,'' tsútkan, ``Kanemlhkán kelh aylh?''
        # ``iy,'' tsút=kan, ``kan-em=lhkán=kelh aylh?''
        # yes say=FSGS do.what=FSGS=FUT then
        # ``Hey,'' I thought, ``What am I gonna do now?''
# - changed + in gloss to = (changed gloss to match seg rather than vice versa, bc these morphemes were each glossed
#   as the corresponding gloss elsewhere)
        # Lhwá7acw es7alkstíts'a7, cuy,'' wa7 tsut.
        # ``lh=wá7=acw es=7alkst-íts'a7, cuy,'' wa7 tsut.
        # COMP+IPFV+SSGC have=work-clothes go.on IPFV say
        # ``If you have work clothes, okay,'' he said.
# - removed extra word in gloss (didn't appear in PDF anyways)
        # Wa7 tsut ``eat, eat.
        # wa7 tsut, ``eat, eat.''
        # IPFV say eat eat this
        # He said, ``Eat, eat.''
# - added LOC gloss for n (appears 9x other times glossed as LOC with the word for teach, to mean school)
        # Xat' káku7 ku wa7 kénki ntsunám'caltena.
        # xat' káku7 ku=wá7 ken=ki=n-tsunám'-cal-ten=a. 
        # hard around+there.INVIS DET=be around=PL.DET=teach-ACT-INS=EXIS
        # It was tough at Residential School.
# - removed extra glosses (VIS,NEG=TC) which were already accounted for in the preceding/followig lines (error from converting PDF)
        # Nas píxem'.
        # nas píxem'.
        # VIS go hunt NEG=TC
        # Go hunting.
# - changed from+DET to from=DET, to align with seg line and bc that's how it was glossed in the word for "ten"
        # Np'a7cw lhelkú xetspqíqin'kst lhnúkwas, t'u7 qicwin'tánemwit láti7.
        # n-p'a7cw lhel=ku=xetspqíqin'kst lh=núkw=as, t'u7 qicw-in'-tánemwit láti7.
        # LOC-more.than from+DET=one.hundred COMP=some=TC but chase-DIR-TPlo+FPLE at+there.VIS
        # There were more than 100 sometimes, but we chased them away.
# - changed to+DET to to=DET, which is how e=ta is glossed elsewhere, including in this line (creates seg/gloss alignment)
        # T'ák.wit, xát'emwit áta7 éta sxál'pta, ts'itemwít éta kwv𝚕̲él'7a.
        # t'ák=wit, xát'em=wit áta7 e=ta=sxál'pt=a, ts'item=wít e=ta=kw𝚕̲·él'·7=a.
        # go.along=TPl climb=TPl to+there.VIS to=DET=Mission.Mountain=EXIS go.towards=TPl to+DET=green·CRED·little.green.place=EXIS
        # They went along, they climbed up Mission Mountain, and then they went towards Kw𝚕̲él'a7 (`Little Green Place').
# - changed PL.DET=TRED·woman to PL.DET=TRED·woman=EXIS, for seg/gloss alignment, and bc that's how it's glossed 2x elsewhere
        # Lkw7u sqáyt.sa áku7 ta Mission Mountaina lhus tsicw q'weláw'em i smelhmúlhatsa icín'as.
        # l=kw7u s-qáyt-s=a áku7 ta=Mission Mountain=a lhus tsicw q'weláw'-em i=smelh·múlhats=a i=cín'=as.
        # at=that.INVIS NMLZ-top-TP=EXIS to+there.INVIS DET=Mission Mountain=EXIS COMP+IPFV+TC get.there pick.berries-MID PL.DET=TRED·woman when.PAST=long.time=TC
        # A long time ago, some women went up to the top of Mission Mountain to pick berries.
# - changed DET=NMLZ=house-SSGP=EXIS to DET=house-SSGP=EXIS for seg/gloss alignment, and bc it appears like that 1x elsewhere, and there just isn't a nominalizer there (tsitcw is just house - it's used plenty) 
        # Cuy,'' tsut ku7 ta sqáycwa, ``Náskalh kelh áku7 úxwal' ta tsítcwswa, láku7 kelh lhmaysentsímas.
        # ``cuy,'' tsút=ku7 ta=sqáycw=a, + ``nás=kalh=klh áku7 úxwal' + ta=tsítcw-sw=a, láku7=kelh [lh]=mays-en-tsí-m=as.''
        # go.on say=QUOT DET=man=EXIS go=FPLS=FUT to+there.INVIS go.home DET=NMLZ=house-SSGP=EXIS at+there.INVIS=FUT COMP=get.fixed-DIR-SSGO-FPLE=TC
        # ``Okay,'' said the man, ``We'll go over to your house and we'll fix you up there.''

# - removed whole affixes which appeared in parentheses in the seg line but did NOT appear in the orthographical line - x31:
#   - those where only the seg line was modified - x11:
        # 'Ats'xenem láti7 sxzúmtens láku7 ta ts'íp'tena k'em'qsts ta tmícwlhkalha.
        # (na) áts'x-en-em láti7 sxzúm-ten-s láku7 ta=ts'íp'-ten=a k'em'-qs-ts ta=tmícw-lhkalh=a.
        # get.seen-DIR-FPLE at+there.VIS big-INS-TP at+there.INVIS DET=cold-INS=EXIS end-point-TP DET=land-FPLP=EXIS
        # We looked at the size of the glacier at the end of our land.

    #   - had to also fix the spacing in the corresponding spot in the gloss line in this one:
        # Lhelkw7á t'u7 álts'q7a lhus qwetsp ta wa7 t'akstumúl'apas káku7 ken kwaláp alkst.
        # ``lhel=kw7á=t'u7 álts'q7=a lhus qwets-p ta=wá7 (a) t'ak-s-tumúl'ap-as káku7 ken=kwaláp alkst.''
        # from=this.INVIS=EXCL outside=EXIS COMP+IPFV+TC move-INCH DET=IPFV   go.along-CAUS-SPLO-TE around+there.INVIS around=DET+NMLZ+IPFV+SPLP work
        # ``Just out here is where that speeder starts that will take you all to where you'll be working.''

        # Tsúntsas ta naplíta, ``Q'wégwen slhécwqswa.
        # (n) tsún-ts-as ta=naplít=a, ``q'wégw-en [ta]=slhécw-q-sw=a.''
        # say+DIR-FSGO-TE DET=priest=EXIS low-DIR DET=put.on-behind-SSGP=EXIS
        # The priest told me, ``Take your pants down.''

        # Tsúntsas, ``Náskacw í7wa7min áti7 sPeter.
        # (sa) tsún-ts-as, ``nás=kacw í7wa7-min áti7 s=Peter.''
        # say+DIR-FSGO-TE go=SSGS accompany-RLT to+there.VIS NMLZ=Peter
        # Then he told me, ``Go with Peter.'

    #   - another spacing fix in the gloss line:
        # Wa7 sk'7aka7mínas láti7 ta srápa, nilh swas scátcen ta q'útqa sq'waxt.s láti7, súpcnam' xílem ku úcwalmicw.
        # wa7 s-k'7-aka7-mín-as láti7 ta=sráp=a, nilh swas s-cát-cen ta=q'út-q=a sq'waxt-s láti7, (supúc) súp-cn-am' xíl-em ku=7úcwalmicw.
        # IPFV STAT-lean-arm-RLT-TE at+there.VIS DET=tree=EXIS COP NMLZ+IPFV+TP STAT-lift-foot DET=one.side-leg=EXIS foot-TP at+there.VIS   scratch-foot-MID do-MID DET=indigenous.person
        # It was leaning its arm against a tree and lifting up one leg, scratching its foot like a person.

        # Wa7 aylh t'iq káti7 i s7ícwlha, lánlhkalh kelh legwápa káti7.
        # (ns...) wa7 aylh t'iq káti7 i=s-7ícwlh=a, lán=lhkalh=kelh [ka]-legw-áp-a káti7.
        # IPFV then arrive around+there.VIS PL.DET=STAT-different=EXIS already=FPLS=FUT CIRC-hide-back-CIRC around+there.VIS
        # So when some strangers came in, we had already gone to hide.

    #   - another spacing fix in the gloss line:
        # T'u7 zam' stsut.s na nspápez7a láti7, ``Wa7 kelh zacensqaxa7cítsim áku7 kwelh s7ílhensu, stem'tétem'su wi snímulh.
        # t'u7 zam' s=tsut=s na=n-spápez7=a láti7, ``wá7=kelh zacen-sqaxa7-cí[t]-tsi-m áku7 kwelh=s7ílhen-su, stem'tétem'-su (s) wi=snímulh.''
        # EXCL after.all NMLZ=say=TP ABS.DET=FSGP-grandfather=EXIS at+there.VIS IPFV=FUT pack-animal-IND-SSGO-FPLE to+there.INVIS PL.INVIS.DET=food-SSGP clothes-SSGP   PL=FPLI
        # But then my grandfather said: ``We can pack your food and clothes up there ourselves.''
    
    #   - another spacing fix in the gloss line:
        # T'iq aylh i sqáyqeycwa tsicw píxem'.
        # t'iq aylh i=sqáy·qeycw=a (lh) tsicw píxem'.
        # arrive then PL.DET=TRED·man=EXIS   get.there hunt
        # Then the men that went out hunting came back.

    #   - another spacing fix in the gloss line:
        # Nilh ses tsúnas láti7 ta kwtámtssa ti smúlhatsa, ``Kanmás k'a aoz kwas kenshal'acitumúlhas láti7 ta skalúl7a ta skuza7lhkálha?''
        # nilh ses (tsut) tsún-as láti7 ta=kwtámts-s=a ti=smúlhats=a, ``kan-m=ás=k'a aoz kwas kens-hal'a-ci[t]-tumúlh-as láti7 ta=skalúl7=a ta=skuza7-lhkálh=a?''
        # COP NMLZ+IPFV+TP   say+DIR-TE at+there.VIS DET=husband-TP=EXIS DET=woman=EXIS do.what-MID=TC=EPIS NEG DET+IPFV+TP want.to-show-IND-FPLO-TE at+there.VIS DET=owl=EXIS DET=offspring-FPLP=EXIS
        # So the woman said to her husband, ``I wonder why the owl doesn't want to show us our child?''

    #   - another spacing fix in the gloss line:
        # Nilh ses matq úxwal', kaxwál'a láti7.
        # nilh ses matq (s) úxwal', ka-xwál'-a láti7.
        # COP NMLZ+IPFV+TP walk   go.home CIRC-crestfallen-CIRC at+there.VIS
        # So he walked home, crestfallen.

    #   - note that the following example involves the segmentation:
        # Wa7 t'u7 aylh, nilh ska7a7masása láti7 ta sm'ém'lhatsa láku7.
        # wá7=t'u7 aylh, nilh s=(a...) ka-7a·7·ma-s-ás-a láti7 ta=sm'é·m'·lhats=a láku7.
        # IPFV=EXCL then COP NMLZ= CIRC-good·CRED·CAUS-TE-CIRC at+there.INVIS DET=woman·CRED·=EXIS at+there.INVIS
        # So then he fell in love with a girl over there.

    #   - note that this example was already modified by a two-line issue, as described in the next section:
        # Aoz t'u7 kwas úts'qa7sas ku skánem.
        # áoz=t'u7 kwas (k') úts'qa7-s-as ku=skán-em.
        # NEG=EXCL DET+NMLZ+IPFV+TP go.out-CAUS-TE DET=do.what-MID
        # He didn't let her out for any reason.


#   - those where the seg AND gloss lines were modified (because the affix was given a gloss) - x20:
        # Tqilh t'u7 n7í7z'ek i kwt'ústensa ta sw'úw'ha lhqám'tas, lkw7a st'épsa ta nxáw'nketssa lh7úts'q7as ta qusmál'tsa.
        # tqílh=t'u7 n7í7z'ek i=kwt'ústen-s=a ta=sw'úw'h=a lh=qám't=as, l=kw7a (t'ép=a) [s]-t'ép-s=a ta=n-xáw'n-k-ets-s=a lh=7úts'q7=as ta=qus-m-ál'ts=a.
        # almost=EXCL in.the.middle PL.DET=eye-TP=EXIS DET=cougar=EXIS COMP=get.hit=TC at=this.INVIS deep=EXIS NMLZ-deep-TP=EXIS DET=LOC-lower-back-mouth-TP=EXIS COMP=go.outside=TC DET=shoot-MID-rock=EXIS
        # It was almost in between the cougar's eyes where it was hit, and it was underneath the lower jaw where the bullet came out.

        # Nilh swas wa7 láku7 sca7s áku7 ta kwímtscena stswaw'c, ltsa xwelcálwit i sám7a i szíka.
        # nilh swas wa7 láku7 s-ca7-s áku7 ta=kwímtscen=a stswaw'c, (ta) l=tsa xwel-cál=wit i=sám7=a i=szík=a.
        # COP NMLZ+IPFV+TP be at+there.INVIS NMLZ-high-TP to+there.INVIS DET=rainbow=EXIS creek DET at=DET+NMLZ+IPFV+TP+EXIS saw-ACT=TPl PL.DET=white.person=EXIS PL.DET=log=EXIS
        # This was above Rainbow Creek, where the white people had a sawmill.

        # Láti7 lhkel7án áts'xen tákem i núkwa úcwalmicw.
        # láti7 lh=kel7=án áts'x-en (i...) tákem i=núkw=a úcwalmicw.
        # at+there.VIS COMP=first=FSGC get.seen-DIR PL.DET all PL.DET=other=EXIS indigenous.person
        # That's when I first saw other people.

        # Nilh sqwal'enítas sPete múta7 Walter Leach pináni7 wa7 qan'im'tsán'an kwas ucwalmícwts, ts'íla ta nqwal'uttenlhkálha.
        # nilh sqwal'-en-ítas s=Pete múta7 Walter Leach pináni7 (wa7) wa7 qan'im'-ts-án'-an [kwas] ucwalmícw-ts, ts'íla ta=n-qwal'ut-ten-lhkálh=a.
        # COP speak-DIR-TPle NMLZ=Pete and Walter Leach at.that.time IPFV IPFV hear-mouth-DIR-FSGE DET+NMLZ+IPFV+TP indigenous.person-mouth like DET=LOC-speak-INS-FPLP=EXIS
        # They asked Pete and Walter Leach, the ones who I understood, to speak Indian, our own language.

        # Nilh zam' láti7 i wa7 maysentáli lheltsá ts7as i sts'ák'wkalha.
        # nilh zam' láti7 i=wa7=mays-en-táli (i...) lhel=tsá ts7as i=sts'ák'w-kalh=a.
        # COP after.all at+there.VIS PL.DET=IPFV=get.fixed-DIR-NTS PL.DET from=DET+NMLZ+IPFV+TP+EXIS come PL.DET=light-FPLP=EXIS
        # These were the people who built the power plant (BC Electric).

        # Cwákenem láti7, wa7 sáwenem:  ``Kacw kánem?
        # cwák-en-em láti7 (wa7 tsún...) wa7 sáw-en-em, ``kacw kán-em?''
        # get.woken-DIR-FPLE at+there.VIS IPFV say+DIR IPFV ask-DIR-FPLE SSGS do.what-MID
        # We woke her up and asked her, ``What are you doing?''

        # 'Aoza kelh múta7 kwásu kateqqwám'mina káti7 kwelh wa7 alkstánacw.
        # ``áoz=a=kelh múta7 kwásu ka-teq-qw-ám'-min-a (láti7) káti7 kwelh=wa7=alkst-án-acw.''
        # NEG=A=FUT again DET+NMLZ+IPFV+SSGP CIRC-touch-top-MID-RLT-CIRC at+there.VIS around+there.VIS PL.INVIS.DET=IPFV=work-DIR-SSGE
        # ``You wouldn't have been able to grasp anything you were working with.''

        # Akú::7 zam' elh tsicw áku7 ki tsilikútena, nilh na tsal'álha áku7, talh7ál'ksa i sqwéma lhus tsícwecw, t'u múta7 p'an't ta cwelelpéka áku7 ta wa7 tsúnem t'ek'wt'ét'k'w, nilh zam' ta Mud Lakesa.
        # [a]kú::7 zam' elh tsicw áku7 (ta...) ki=tsilikúten=a, nilh (s) na=tsal'álh=a áku7, talh7-ál'k-s=a i=sqwém=a lhus tsícw·ecw t'u múta7 p'an't ta=cwel·el-p-ék=a áku7 ta=wa7=tsún-em t'ek'w·t'é·t'·k'w, nilh zam' ta=Mud Lakes=[a].
        # to+there.INVIS though and.then get.there to+there.INVIS DET PL.DET=Chilcotin=EXIS COP NMLZ ABS.DET=lake=EXIS to+there.INVIS other.side-surface-TP=EXIS PL.DET=mountain=EXIS COMP+IPFV+TC get.there·FRED until again return DET=revolve·FRED-INCH-back=EXIS to+there.INVIS DET=IPFV=say+DIR-TSG.PASS TRED·lake·CRED· COP after.all DET=Mud Lakes=EXIS
        # The helicopter went over to Chilcotin country, and got as far as a lake on the other side of the mountains until it returned back to what they call ``many little lakes'', that's the, ``Mud Lakes.''

        # 'An'was k'a láti7 sxetspásq'et kw nswa7 elh nzewátet.skan i k'wína sám7ats.
        # án'was=k'a láti7 sxetspásq'et (kw=n=s=wa7...) kw=n=s=wa7 elh n-zewát·et-s=kan i=k'wín=a sám7a-ts.
        # two=EPIS at+there.VIS week DET=FSGP=NMLZ=be DET=FSGP=NMLZ=be and.then LOC-be.known·FRED-CAUS=FSGS PL.DET=how.much=EXIS white.person-mouth
        # It must've been two weeks before I learned a few words in English.

        # Nilh t'u7 nstqilh lhápen ta tsuwa7lhkálha nqwal'útten múta7 nt'ákmen, nilh tsa papt wa7 sekentúmulem lhwas qwezeném ta tsuwa7lhkálha nqwal'útten.
        # nílh=t'u7 (s...) n=s=tqilh lháp-en ta=tsuwa7-lhkálh=a n-qwal'út-ten múta7 nt'ákmen, nilh tsa papt wa7 sek-en-túmulem lhwas qwez-en-ém ta=tsuwa7-lhkálh=a n-qwal'út-ten.
        # COP=EXCL NMLZ FSGP=NMLZ=almost get.forgotten-DIR DET=own-FPLP=EXIS LOC-speak-INS and traditional.way.of.life COP DET+NMLZ+IPFV+TP+EXIS always IPFV get.whipped-DIR-FPL.PASS COMP+IPFV+TC get.used-DIR-FPLE DET=own-FPLP=EXIS LOC-speak-INS
        # I just about forgot our language and our ways, because we were always getting hit when we used our own language.

        # Nilh t'u7 nsgelílcmin kw nskap'án't.sa tákem ta ntsúw7a nqwal'útten.
        # nílh=t'u7 (s...) n=s=gel-ílc-min kw=n=s=ka-p'án't-s-a tákem [ta]=n-tsúw7=a n-qwal'út-ten.
        # COP=EXCL NMLZ FSGP=NMLZ=strong-Aut-RLT DET=FSGP=NMLZ=CIRC-return-CAUS-CIRC all DET=FSGP-own=EXIS LOC-speak-INS
        # So I did my best to get my language back.

        # Nilh t'u7 scuz' cwaz'an'ítas i ucwalmícwa.
        # ``nílh=t'u7 s=cuz' (cwaz'-an'-ítas) cwaz'-an'-ítas i=7ucwalmícw=a.''
        # COP=EXCL NMLZ=going.to disappear-DIR-TPle disappear-DIR-TPle PL.DET=indigenous.person=EXIS
        # ``They're going to eliminate indigenous people.''

        # Lan k'a tu7 kacwáz'a kwas ucwalmícwwit.
        # ``(lán=k'a...) lán=k'a=tu7 ka-cwáz'-a kwas ucwalmícw=wit.''
        # already=EPIS already=EPIS=REM CIRC-disappear-CIRC DET+NMLZ+IPFV+TP indigenous.person=TPl
        # ``They have already been extinguished as indigenous people.''

    #   - note that the following example involves the segmentation:
        # T'ak ka t'u7 tsunam'enítas i sk'wemk'úk'wmi7ta kw stexw kateqstwítasa ta nqwal'uttenlhkálha kw swa7 múta7 tsunam'enítas kwelh tsúw7i stsmal't láti7 kw skap'án't.sa, kap'an't.stúma tákem, kw scw7aoys cwaz'an'tumúlem kwat úcwalmicw.
        # ``t'ák=ka=t'u7 tsunam'-en-ítas i=sk'wem·k'úk'wmi7t=a kw=s=stexw ka-(téq-s-a...) teq-s-twítas-a ta=n-qwal'ut-ten-lhkálh=a kw=s=wa7 múta7 tsunam'-en-ítas kwelh=tsúw7-i stsmal't...'' ``láti7 kw=s=ka-p'án't=s-a, [ka]-p'an't-s-túm-a tákem, kw=s=cw7aoy=s cwaz'-an'-tumúlem kwat úcwalmicw.''
        # continue=IRR=EXCL teach-DIR-TPle PL.DET=TRED·child=EXIS DET=NMLZ=really CIRC-touch-CAUS-CIRC touch-CAUS-TPle-CIRC DET=LOC-speak-INS-FPLP=EXIS DET=NMLZ=IPFV again teach-DIR-TPle PL.INVIS.DET=own-TPlp children at+there.VIS DET=NMLZ=CIRC-return=TP-CIRC CIRC-return-CAUS-TSG.PASS-CIRC all DET=NMLZ=NEG=TP disappear-DIR-FPL.PASS DET+NMLZ+IPFV+FPLC indigenous.person
        # ``They should keep on teaching the children so that they can really grasp the language, so that they in turn can teach their own children...'' ``so that it can come back, and everything can be restored, and then they will not be able to eliminate us as indigenous people.''

        # Wá7as t'u7 gelílc, áma ta nscwákwekwa tsa wa7 gelilcmínas kwas wa7 iy, i núkwa wa7 qan'ím'ts kw swa7 katsunam'calwíta.
        # wá7=as=t'u7 gel-ílc, áma ta=n-scwákwekw=a tsa wa7 gel-ilc-mín-as kwas wa7 iy, i=núkw=a wa7 qan'ím'-ts kw=s=wa7 (ka...) ka-tsunam'-cal=wít-a.
        # IPFV=TC=EXCL strong-Aut good DET=FSGP-heart=EXIS DET+NMLZ+IPFV+TP+EXIS IPFV strong-Aut-RLT-TE DET+NMLZ+IPFV+TP IPFV yes PL.DET=other=EXIS IPFV hear-mouth DET=NMLZ=IPFV CIRC CIRC-teach-ACT=TPl-CIRC
        # May she just keep trying hard, I am glad she is doing her best so that others can understand how to teach the language.

        # Skéla7s ti7 múta7 kw nsxát'em áku7 éta skela7lhkálha xát'em.
        # [s]=kéla7=s ti7 múta7 kw=n=s=xát'em áku7 (ta) e=ta=s=kela7=lhkálh=a xát'-em;
        # NMLZ=first=TP that.VIS and DET=FSGP=NMLZ=climb to+there.INVIS DET to=DET=NMLZ=first=FPLP=EXIS climb
        # Where we went up at the beginning, that was the first time I'd taken that route;

        # Lhláti7 aylh múta7 lhp'án'tat áku7 ltsa sgaz nelh k'ét'ha, láti7 lhcín'as kw swá7lhkalh.
        # lhláti7 aylh múta7 lh=p'án't=at áku7 (ta...) l=tsa s-gaz nelh=k'ét'h=a, láti7 lh=cín'=as kw=s=wá7=lhkalh.
        # from+there.VIS then again COMP=return=FPLC to+there.INVIS DET at=DET+NMLZ+IPFV+TP+EXIS STAT-piled.up PL.ABS.DET=rock=EXIS at+there.VIS COMP=long.time=TC DET=NMLZ=be=FPLP
        # From there we went back again to where the rocks are piled up, we stayed there for a long time.

        # S7i7cwlh lta suxwastkálha.
        # s7i·7·cwlh (ta) l=ta=suxwast=kálh=a.
        # different·CRED· DET at=DET=go.downhill=FPLP=EXIS
        # We went a little different way when we went down.

        # Nilh ti7 kaptinusmínana láku7 iwás áts'xenem láku7 tákem i sqwémqwema.
        # nílh=ti7 ka-ptinus-mín-an-a láku7 i=wás áts'x-en-em láku7 (ta) tákem i=sqwém·qwem=a.
        # COP=that.VIS CIRC-think-RLT-FSGE-CIRC at+there.INVIS when.PAST=IPFV+TC get.seen-DIR-FPLE at+there.INVIS DET all PL.DET=TRED·mountain=EXIS
        # That's what I was thinking about when we were looking at all the mountains there.

        # Púpen'lhkan láti7 i... 
        # pú·p·en'=lhkan láti7 i(n)...
        # get.found·CRED·+DIR=FSGS at+there.VIS PL.DET
        # I came across some...

# - fixed adjacent lines where one word was on the wrong line (sometimes. incl changes to periods or spaces) x8 sets
        # 'Ats'xenas láti7 ta núkwa.
        # áts'x-en-as láti7 ta=núkw=a. 
        # get.seen-DIR-TE at+there.
        # She looked over at the other one, he was a good trapper.

        # Texw t'u7 á7xa7 ku q'w7um, nilh t'u7 ses tsut, ets'7áts'xenas láti7, kakv𝚕̲'min'ása múta7 láti7... t'u7... kaptínusema ``Aoz.
        # téxw=t'u7 á7xa7 ku=q'w7-úm, nílh=t'u7 ses tsut, ets'·7áts'x-en-as láti7, ka-kv𝚕̲'-min'-ás-a múta7 láti7... t'u7... ka-ptínus-em-a, ``aoz.''
        # DET=other=EXIS really=EXCL powerful DET=trap-MID COP=EXCL NMLZ+IPFV+TP think TRED·get.seen-DIR-TE at+there.VIS CIRC-catch.sight.of-RLT-TE-CIRC again at+there.VIS EXCL CIRC-think-MID-CIRC NEG
        # So she thought about it, looked him over, glanced at him one more time, but then decided, ``No.''


        # Nilh aylh zam' múta7 sts'ílas ku sk'á7sas láku7 ta sm'ém'lhatsa.
        # nilh aylh zam' múta7 s=ts'íla=s ku=s-k'á7-s-as láku7 ta=sm'é·m'·lhats=a.
        # COP then after.all again NMLZ=like=TP DET=STAT-get.put.in.jail-CAUS-TE to+there.
        # Then after all that, he kind of kept the young woman in jail. 

        # Aoz t'u7 kwas úts'qa7sas ku skánem.
        # áoz=t'u7 kwas (k') úts'qa7-s-as ku=skán-em.
        # DET=woman·CRED·=EXIS NEG=EXCL DET+NMLZ+IPFV+TP   go.out-CAUS-TE DET=do.what-MID
        # He didn't let her out for any reason.


        # Nilh k'a ti7 wa7 tsúnitas i sám7a cá7a tmicw.
        # nilh=k'á=ti7 wa7 tsún-itas i=sám7=a cá7=a tmicw. Paradise.
        # COP=EPIS=that.VIS IPFV say+DIR-TPle PL.DET=white.person=EXIS high=EXIS land paradise
        # That must be why the white people call it ``Paradise.''

        # Paradise.  Tqílhkan t'u7 láku7... wá7al'men láku7 t'u7 wá7lhkan t'u7 múta7 uxwal'ál'men láti7.
        # tqílh=kan=t'u7 láku7... wá7-al'men láku7 t'u7 wá7=lhkan=t'u7 múta7 uxwal'-ál'men láti7.
        # almost=FSGS=EXCL at+there.INVIS be-wish.to at+there.INVIS but IPFV=FSGS=EXCL again go.home-wish.to at+there.VIS
        # I almost wanted to just stay there but I also wanted to go home again.


        # Nas et7ú gap, nilh s...  Cwákkan.
        # nas e=t7ú gap, nilh s=...
        # go to=that.VIS evening COP NMLZ= 
        # It was getting towards evening and...

        # Lánlhkan aylh wa7 ícwa7 esgítsmen.
        # cwák=kan. lán=lhkan aylh wa7 ícwa7 es=gítsmen.
        # get.woken=FSGS already=FSGS then IPFV without have=teeth
        # I woke up. And I had no teeth at all.


        # Xmank7úl láti7 ta cá7a, nilh szet'q's. ``Yeah,'' kan tsúnwit, ``Cúy'lhkan tsukw: xat' láku7 lts7a s7alkst.
        # xmank-7úl láti7 ta=cá7=a, nilh s=zet'q'=s.
        # heavy-real at+there.VIS DET=high=EXIS COP NMLZ=collapse=TP
        # The upper bank was too heavy, that's why it crumbled.

        # K'ínk'ent.
        # ``Yeah,'' kan tsún-wit, ``cúy'=lhkan tsukw: xat' láku7 l=ts7a s7alkst. k'ínk'ent.''
        # yeah FSGS say+DIR-TPlo going.to=FSGS finish hard at+there.INVIS at=this.VIS work dangerous
        # ``Yeah,'' I told them, ``I'm gonna quit: This is hard work, and dangerous.''


        # O,'' tsut, ``Qv𝚕̲ iz'.
        # ``o,'' tsut, ``q'v𝚕̲=iz'. áoz=kelh kw=s=xwém=su lhaxw lh=cuz'=acw=t'ú7=iz' we7-án.''
        # oh say bad=those.VIS NEG=FUT DET=NMLZ=fast=SSGP get.healed COMP=going.to=SSGC=EXCL=those.VIS be-DIR
        # ``Oh,'' he said, ``Those are no good. You won't heal fast if you still have those.''

        # Aoz kelh kw sxwémsu lhaxw lhcúz'acw t'ú7 iz' we7án.
        # ``o,'' kan tsun, ``cúy'=lhkacw aylh zam' kán-em?''
        # oh FSGS say+DIR going.to=SSGS then after.all do.what-MID
        # ``Oh,'' I asked him, ``What are you going to do then?''

        # O,'' kan tsun, ``Cúy'lhkacw aylh zam' kánem?'' ``O, tsekweném kelh iz' tákem.
        # ``o, tsekw-en-ém=klh=iz' tákem.''
        # oh get.pulled-DIR-FPLE=FUT=those.VIS all
        # ``Oh, we'll pull them all out.''


        # Lkw7u lhkel7án tsicw ta wa7 tsúnitas West Fraser, áku7 zam'
        # l=kw7u lh=kel7=án tsicw ta=wa7=tsún-itas West Fraser...
        # at=that.INVIS COMP=first=FSGC get.there DET=IPFV=say+DIR-FPLE West Fraser
        # I first went over to West Fraser...

        # Prince George, elh áku7 Fraser Lake.
        # ...áku7 zam' Prince George, elh áku7 Fraser Lake.
        # to+there.INVIS after.all Prince George and.then to+there.INVIS Fraser Lake
        # ...then over to Prince George, and then up to Fraser Lake.

        # O,'' wa7 tsut, ``Cw7it káti7 i wa7 zíkam.
        # ``o,'' wa7 tsut, ``cw7it káti7 i=wa7=zík-am. nás=kacw zík-am.''
        # oh IPFV say many around+here.VIS PL.DET=IPFV=log-MID go=SSGS log-MID
        # ``Oh,'' he said, ``There's a lot of logging going on around. Go try logging.''

        # Náskacw zíkam.  Nzewátet.s káti7 kw kánem lhus wa7 i wa7 zíkam.
        # ``n-zewát·et-s káti7 kw=kán-em lhus wa7 i=wa7=zík-am.''
        # LOC-be.known·FRED-CAUS around+here.VIS DET=do.what-MID COMP+IPFV+TC IPFV PL.DET=IPFV=log-MID
        # ``Learn how to do what they do when they're logging.''

#   - similarly, these ones required some edits to its line breaks (in the gloss and translation lines)
        # Kent7ú cá7a t'it, kénta sqwéqwem'a láti7 s7áw't.sa láti7 ta... stám'as k'á hem' kw snahs i barna? ltsa tsicw p'i7almicwenítas i músmusa, s7áw't.s áku7 lhas ri7p i sq'wéla láti7 – áopv𝚕̲s, tsális, pas, apricots, tákem t'u7.
        # ken=t7ú cá7=a t'it, + ken=ta=sqwé·qw·em'=a láti7 + s-7áw't-s=a ta... + stam'=as=k'á=hem' kw=s-nah-s + i=barn=a? l=tsa + tsicw p'i7-almicw-en-ítas + i=músmus=a s-7áw't-s áku7 lhas ri<7>p i=sq'wél=a láti7: áopv𝚕̲s, tsális, pas, apricots, tákem=t'u7.
        # around=that.VIS high=EXIS also around=DET=mountain·CRED·=EXIS NMLZ-behind-TP to+there.VIS COMP+IPFV+TC grow<INCH> PL.DET=berry=EXIS at+there.VIS apple cherry pear apricots all=EXCL
        # at+there.VIS NMLZ-behind-TP=EXIS DET what=TC=EPIS=ANTI DET=NMLZ-name-TP PL.DET=barn=EXIS at=DET+NMLZ+IPFV+TP+EXIS get.there squeeze-udder-DIR-TPle PL.DET=cow=EXISUp higher on a hill behind the – what's the name for a barn? – where they went to milk the cows behind there is where the fruit grew: apples, cherries, pears, apricots, everything.

        # Nilh hem' ti7 zam' aylh kaxéksasa ta nsqátsez7a, wa7 tsúnas láti7 t.snúk'wa7sa wa7 qwa7yán'ak, nilh t'u7 aylh lhus nq'san'kmínitas láti7, nilh t'u7 s7aylhts t'u7 ti7 aylh t'u7 skwátsitss, Qwa7yán'ak.
        # nílh=hem'=ti7 zam' aylh ka-xék-s-as-a ta=n-sqátsez7=a, wa7 tsún-as láti7 t=snúk'wa7-s=a wa7 ``qwa<7>y-án'ak'', nílh=t'u7 aylh lhus n-q's-an'k-mín-itas láti7 nílh=t'u7 s=7aylh=ts=t'ú7=ti7, áylh=t'u7 skwátsits-s, ``Qwa<7>y-án'ak''. 
        # COP=ANTI=that after.all then CIRC-reckon-CAUS-TE-CIRC DET=FSGP-father=EXIS COP=EXCL NMLZ=then=TP=EXCL=that then=EXCL name-TP blue<INCH>-stomach
        # IPFV say+DIR-TE at+there.VIS DET=friend-TP=EXIS IPFV blue<INCH>-stomach COP=EXCL then COMP+IPFV+TC LOC-laugh-stomach-RLT-TPle at+there.VISMy father figured that out when he told his friend he was qwa7yán'ak, and they laughed at him and then his name became Qwa7yán'ak after that.


#   - for place names that had a literal gloss and the English name in brackets, I kept only the English name
#   - e.g. gloss of tsal'álh as lake[Shalalth] was replaced with just Shalalth
        # - lake[Shalalth] -> Shalalth x18
        # - confluence.of.rivers[Lytton] -> Lytton x3
        # - get.to.the.top[Mission.Mountain] -> Mission.Mountain x1
        # - close.to.shore[Seton.Portage] -> Seton.Portage x2
        # - eagle.nest[Marshall.Creek] -> Marshall.Creek x2
        # - lots.of.balsam.roots[Camoo] -> Camoo x3 (note that this one is Sexwemáwt in every other line?)
        # - female.mountain.sheep[Yalakom] -> Yalakom x1
        # - [little.green.place] -> little.green.place x2 (for consistency, this should probably be Kw𝚕̲él'a7 instead)

# - removed whole affixes which appeared in BRACKETS in the seg line but did NOT appear in the orthographical line - x38:
#   - those where the seg AND gloss lines were modified (because the affix was given a gloss) - x18:
        # Nilh t'u7 snilhts láti7 sip'áoz'sa lhélta kwt'ústen'sa t'álhan'as lta q'úmqensa ts'íla ku t'éna7.
        # nílh=t'u7 s=nilh=ts láti7 [ta]=sip'áoz'-s=a lhel=ta=kwt'ús-ten'-s=a t'álh-an'-as l=ta=q'úmqen-s=a ts'íla ku=t'éna7.
        # COP=EXCL NMLZ=COP=TP at+there.VIS DET=skin-TP=EXIS from=DET=face-INS-TP=EXIS stick-DIR-TE on=DET=head-TP=EXIS like DET=ear
        # So then he stuck the skin from his eyes on his head, like ears. 

        # Nilh t'u7 sawenítas i smúlhatsa: ``Kástskacw?''
        # nílh=t'u7 [s]=saw-en-ítas i=smúlhats=a, ``kás-ts=kacw?''
        # COP=EXCL NMLZ=ask-DIR-TPle PL.DET=woman=EXIS how-CAUS=SSGS
        # So they asked the women, ``How did you do it?''

        # Q'áylec láti7 sEugene, nilh t'k'iwlecmínas láti7 ta sqatsza7lhkálha, spaqu7sá t'u7.
        # q'áy-lec láti7 s=Eugene, nilh t'k'iw-lec-mín-as láti7 ta=sqatsza7-lhkálh=a, [t]=s=paqu7=s=á=t'u7.
        # jump-Aut at+there.VIS NMLZ=Eugene COP climb-Aut-RLT-TE at+there.VIS DET=father-FPLP=EXIS DET=NMLZ=afraid=TP=EXIS=EXCL
        # Eugene jumped up and climbed on our father because he was afraid.

        # Nilh ti7 kéla7 zewátenan láti7, kéla7s kw nstsicw káku7 tsunám'caltena.
        # nílh=ti7 kéla7 zewát-en-an láti7, [s]=kéla7=s kw=n=s=tsicw káku7 tsunám'-cal-ten=a.
        # COP=that.VIS first be.known-DIR-FSGE at+there.VIS NMLZ=first=TP DET=FSGP=NMLZ=get.there around+there.INVIS teach-ACT-INS=EXIS
        # That's the first thing I knew, before I went to school.

        # Hey,'' wa7 tsut, ``Aoz t'u7 kw súq'wenacw!''
        # ``hey,'' wa7 tsut, ``áoz=t'u7 kw=[s]=súq'w-en-acw!''
        # hey IPFV say NEG=EXCL DET=NMLZ=skin-DIR-SSGE
        # ``Hey,'' he said, ``You didn't skin it!''

        # 'Ama t'u7 zam', nilh skwamemlhkálha ta ts'í7a, ta k'wína sq'it.
        # áma=t'u7 zam', nilh [t]=s=kwam·em=lhkálh=a ta=ts'í7=a, ta=k'wín=a sq'it.
        # good=EXCL after.all COP DET=NMLZ=get·FRED=FPLP=EXIS DET=deer=EXIS DET=how.many=EXIS day
        # Anyway, the deer we got was good for a few days.

    #   - just the first instance of brackets in this example was modified:
        # Nilh sixin'tsálem éta grade twoa pináni7.
        # nilh [s]=six-in'-tsálem e=ta=grade two=[a] pináni7.
        # COP NMLZ=move-DIR-FSG.PASS to=DET=grade two=EXIS at.that.time
        # They put me up to grade two.

    # - both instances below were modified:
        # Nilh skwantumúlem aylh wi snímulh sk'wemk'úk'wmi7ta ta welfare.
        # nilh s=kwan-tumúlem aylh wi=snímulh [i]=sk'wem·k'úk'wmi7t=a ta=welfare=[a].
        # COP NMLZ=take+DIR-FPL.PASS then PL=FPLI PL.DET=TRED·child=EXIS DET=welfare=EXIS
        # Then the welfare took us children.

        # Nilh láti7 sqlhúl'watkalh láti7 i cúz'a t'áksan, plans k'a láti7 wa7 n7uts'q7álmen.
        # nilh láti7 s=qlh-úl'wat=kalh láti7 i=cúz'=a t'ák-s-an, [s]=plán=s=k'a láti7 wa7 n-7uts'q7-álmen.
        # COP at+there.VIS NMLZ=store-things=FPLP at+there.VIS PL.DET=going.to=EXIS go.along-CAUS-FSGE NMLZ=already=TP=EPIS at+there.VIS IPFV LOC-go.outside-almost
        # We packed up what I was going to take along, since it must've been almost spring.

        # Nilh paqu7mínan láti7 kwes kelh zuqwstumcalítas láti7 lh7áozas kw nszewátet.s, 
        # nilh [s]=paqu7-mín-an láti7 + kwés=kelh + zuqw-s-tumcal-ítas + láti7 lh=7áoz=as + kw=n=s=zewát·et-s...
        # COP NMLZ=afraid-RLT-FSGE at+there.VIS DET+NMLZ+IPFV+TP=FUT die-CAUS-FSGO-TPle at+there.VIS COMP=NEG=TC DET=FSGP=NMLZ=be.known·FRED-CAUS
        # That's what I was scared of, if I didn't learn to speak English they'd probably kill me...

        # Tsúntsas ta naplíta, ``Q'wégwen slhécwqswa.
        # tsún-ts-as ta=naplít=a, ``q'wégw-en [ta]=slhécw-q-sw=a.''
        # say+DIR-FSGO-TE DET=priest=EXIS low-DIR DET=put.on-behind-SSGP=EXIS
        # The priest told me, ``Take your pants down.''

        # Nilh t'u7 stqilhts k'a kantsqám'a láti7 ta skalúl7a, sts'ílasa kw scw7it.s kw sxat's ta smúlhatsa.
        # nílh=t'u7 s=tqílh=ts=k'a ka-n-tsqám'-a láti7 ta=skalúl7=a... [t]=s=ts'íla=s=a kw=s-cw7it-s kw=s-xat'-s ta=smúlhats=a.
        # COP=EXCL NMLZ=almost=TP=EPIS CIRC-LOC-fall.back-CIRC at+there.VIS DET=owl=EXIS DET=NMLZ=like=TP=EXIS DET=NMLZ-many-TP DET=NMLZ-want-TP DET=woman=EXIS
        # So the owl almost fell backwards because the woman wanted so much.

        # Gap láti7, nilh t'u7 sqwál'enas láti7 kw scúz'i n'an'atcwám lhnásas q'weláw'emwit ta skalúl7a.
        # gap láti7, nílh=t'u7 [s]=sqwál'-en-as láti7 kw=s=cúz'=i n'an'atcw-ám lh=nás=as q'weláw'-em=wit ta=skalúl7=a.
        # evening at+there.VIS COP=EXCL NMLZ=tell-DIR-TE at+there.VIS DET=NMLZ=going.to=TPlp morning-MID COMP=go=TC pick-MID=TPl DET=owl=EXIS
        # It was night, so he told his friend they would get up early to go picking.

        # Sáwlhen aylh skalúl7a: ``kan kw sxílhtum'cacw t'it áti7, kw stewtiwaskálh kelh láti7 amhál'qwem'?''
        # sáwlhen aylh [ta]=skalúl7=a: ``kan kw=s=xílh-tum'c-acw t'it áti7, kw=s=tew·tiwas=kálh=kelh láti7 amh-ál'qwem'?''
        # ask.question then DET=owl=EXIS whether DET=NMLZ=get.done+CAUS-FSGO-SSGE also to+there.VIS DET=NMLZ=TRED·both=FPLS=FUT at+there.VIS good-appearance
        # The owl asked, ``Can you do that to me too, so we'll both look good?''

        # Wa7 aylh t'iq káti7 i s7ícwlha, lánlhkalh kelh legwápa káti7.
        # wa7 aylh t'iq káti7 i=s-7ícwlh=a, lán=lhkalh=kelh [ka]-legw-áp-a káti7.
        # IPFV then arrive around+there.VIS PL.DET=STAT-different=EXIS already=FPLS=FUT CIRC-hide-back-CIRC around+there.VIS
        # So when some strangers came in, we had already gone to hide.

        # Aoz kw nszewáten ku sám7ats pináni7, nilh t'u7 sáwenan ta nsqátsez7a lhus ínwatwit.
        # aoz kw=n=s=zewát-en ku=sám7a-ts pináni7, nílh=t'u7 [s]=sáw-en-an ta=n-sqátsez7=a lhus ínwat=wit.
        # NEG DET=FSGP=NMLZ=be.known-DIR DET=white.person-mouth at.that.time COP=EXCL NMLZ=ask-DIR-FSGE DET=FSGP-father=EXIS COMP+IPFV+TC say.what=TPl
        # I didn't understand any English at all at that time so I asked my father what they were saying.

        # Nilh láti7 skwenkwanaxánnem, nilh súxwast.stum áku7 ta campa.
        # nilh láti7 s=kwen·kwan-axán-n-em, nilh [s]=súxwast-s-tum áku7 ta=camp=a.
        # COP at+there.VIS NMLZ=TRED·take-arm-DIR-FPLE COP NMLZ=go.downhill-CAUS-FPLE to+there.INVIS DET=camp=EXIS
        # We took her by the arms and brought her down to the camp.

        # Sxel' múta7 áku7 ta c.wéw'lha ta suxwastkálha.
        # s-xel' múta7 áku7 ta=c.w·éw'·lh=a ta=[s]=suxwast=kálh=a.
        # STAT-steep again to+there.INVIS DET=road·CRED·=EXIS DET=NMLZ=go.downhill=FPLP=EXIS
        # The trail was steep where we went down.

#   - those where only the seg line was modified - x20:
        # O,'' wa7 tsut láti7 ta smúlhatsa, ``Náskacw q'weláw'cits káti7 ku cw7it stsáqwem.
        # ``o,'' wa7 tsut láti7 ta=smúlhats=a, ``nás=kacw q'weláw'-ci[t]-ts káti7 ku=cw7ít stsáqwem.''
        # oh IPFV say at+there.VIS DET=woman=EXIS go=SSGS pick-IND-FSGO around+there.VIS DET=much saskatoon.berry
        # ``Oh,'' the woman said, ``Go pick me lots of tsáqwem (saskatoon berries).''

        # Wa7 qúlun láti7 kwlha k'win ts'la7, nilh t'u7 sts7áscitsacw.
        # ``wa7 qúl-un láti7 kwlha k'win ts'la7, nílh=t'u7 s=ts7ás-ci[t]-ts-acw''
        # IPFV full-DIR at+there.VIS these.INVIS how.many basket COP=EXCL NMLZ=come-IND-FSGO-SSGE
        # ``Fill a bunch of baskets, and then bring them to me.''

        # Lan ka amacítsin láti7.
        # ``lán=ka ama-cí[t]-tsin láti7.''
        # already=IRR good-IND-SSGO at+there.VIS
        # ``I'll be satisfied with you then.''

        # Nilh ses tsúnas láti7 ta kwtámtssa ti smúlhatsa, ``Kanmás k'a aoz kwas kenshal'acitumúlhas láti7 ta skalúl7a ta skuza7lhkálha?''
        # nilh ses tsún-as láti7 ta=kwtámts-s=a ti=smúlhats=a, ``kan-m=ás=k'a aoz kwas kens-hal'a-ci[t]-tumúlh-as láti7 ta=skalúl7=a ta=skuza7-lhkálh=a?''
        # COP NMLZ+IPFV+TP say+DIR-TE at+there.VIS DET=husband-TP=EXIS DET=woman=EXIS do.what-MID=TC=EPIS NEG DET+IPFV+TP want.to-show-IND-FPLO-TE at+there.VIS DET=owl=EXIS DET=offspring-FPLP=EXIS
        # So the woman said to her husband, ``I wonder why the owl doesn't want to show us our child?''

        # Láku7 k'a zam', láti7 lhwá7as láti7 ta smúlhatsa wa7 eskúza7, ta sm'ém'lhatsa.
        # láku7=k'a zam', láti7 lh=wá7=as láti7 ta=smúlhats=a wa7 es=[s]kúza7, ta=sm'é·m'·lhats=a.
        # at+there.INVIS=EPIS after.all at+there.VIS COMP=be=TC at+there.VIS DET=woman=EXIS IPFV have=offspring DET=woman·CRED·=EXIS
        # A woman lived there that had a young daughter.

    #   - altered the second bracket occurrence here:
        # Plánlhkacw wa7 tsicwaszánucw, lh7áozas kwásu xát'min' ku sqaycw, cuz' kelh á::wcitsim láti7 ku sqaycw, wa7 cuz' skwtámtssu.
        # ``plán=lhkacw wa7 tsicw-[a]szánucw, lh=7áoz=as kwásu xát'-min' ku=sqáycw, cúz'=kelh á::w-ci[t]-tsi-m láti7 ku=sqáycw, wa7 cuz' skwtámts-su.''
        # already=SSGS IPFV get.there-year COMP=NEG=TC DET+NMLZ+IPFV+SSGP want-RLT DET=man going.to=FUT choose-IND-SSGO-FPLE at+there.VIS DET=man IPFV going.to husband-SSGP
        # ``You have come of age, if you don't want any man for a husband, we will choose one for you.''

        # Nq'san'kmínem aylh láti7 i sqáyqeycwa, wa7 tsútwit, ``Kaksépkalha tsicw píxem', aoz kw skwámemlhkalh, k'ámalha snuláp smelhmúlhats, ícwa7 eswelmín'k láti7,  meskal'áp t'u7 zam' zúqwnucw ta st'alhálema.
        # n-q's-an'k-mín-em aylh láti7 i=sqáy·qeycw=a, wa7 tsút=wit, ``ka-ksép=kalh-a tsicw píxem', aoz kw=s=kwám·em=lhkalh, k'ámalh=a snuláp smelh·múlhats... ícwa7 es=[s]welmín'k láti7,  mes=kal'áp=t'u7 zam' zúqw-nucw ta=st'alhálem=a.''
        # LOC-laugh-stomach-RLT-TSG.PASS then at+there.VIS PL.DET=TRED·man=EXIS IPFV say=TPl CIRC-go.far=FPLS-CIRC get.there hunt NEG DET=NMLZ=get·FRED=FPLP however=A SPLI TRED·woman without have=gun at+there.VIS but=SPLS=EXCL after.all kill-game DET=grizzly.bear=EXIS
        # The men laughed at the women and they said, ``We went a long ways to hunt and we never caught anything. But you women, you didn't have any guns, and you killed a grizzly bear.''

        # T'u7 zam' stsut.s na nspápez7a láti7, ``Wa7 kelh zacensqaxa7cítsim áku7 kwelh s7ílhensu, stem'tétem'su wi snímulh.
        # t'u7 zam' s=tsut=s na=n-spápez7=a láti7, ``wá7=kelh zacen-sqaxa7-cí[t]-tsi-m áku7 kwelh=s7ílhen-su, stem'tétem'-su wi=snímulh.''
        # EXCL after.all NMLZ=say=TP ABS.DET=FSGP-grandfather=EXIS at+there.VIS IPFV=FUT pack-animal-IND-SSGO-FPLE to+there.INVIS PL.INVIS.DET=food-SSGP clothes-SSGP PL=FPLI
        # But then my grandfather said: ``We can pack your food and clothes up there ourselves.'

        # Nswa t'u7 tsáylec káti7 lhus t'at'imcetscitumúlhas láti7 i slalil'temlhkálha.
        # nswá=t'u7 tsáy-lec káti7 lhus t'at'-imc-ets-ci[t]-tumúlh-as láti7 i=slalil'tem-lhkálh=a.
        # FSGP+NMLZ+IPFV=EXCL crawl-Aut around+there.VIS COMP+IPFV+TC Fraser.River-people-mouth-IND-FPLO-TE at+there.VIS PL.DET=parents-FPLP=EXIS
        # I was crawling around when our parents began speaking St'át'imcets to us.

        # Náscitsas láti7 ka7lhás qusemál'ts.
        # nás-ci[t]-ts-as láti7 ka7lhás qus-em-ál'ts.
        # go-IND-FSGO-TE at+there.VIS three shoot-MID-rock
        # He gave me three bullets.

        # Nilh tsukw spíxem'lhkalh ta pál7a múta7 t'ánam'ten láti7, kwat wa7 es7ílhen.
        # nilh tsukw s=píxem'=lhkalh ta=pál7=a múta7 t'ánam'ten láti7, kwat wa7 es=[s]7ílhen.
        # COP finish NMLZ=hunt=FPLP DET=one=EXIS again moon at+there.VIS DET+NMLZ+IPFV+FPLC IPFV have=food
        # We didn't hunt for one month again, since we had food.

        # Ao7z'álh t'u7 kwenswá zewáten ku sám7ats pináni7, nilh ses aw'tetscitsalítas.
        # ao<7>z'-álh=t'u7 kwenswá zewát-en ku=sám7a-ts pináni7, nilh ses aw't-ets-ci[t]-tsal-ítas.
        # NEG<INCH>-utmost=EXCL DET+FSGP+NMLZ+IPFV be.known-DIR DET=white.person-mouth at.that.time COP NMLZ+IPFV+TP behind-mouth-IND-FSGO-TPle
        # I didn't know English at that time, so they translated for me.

        # Tqilh k'a án'was t'ánam'ten láti7 kwas wa7 ta wa7 n7aw'tetscítsas láti7 i sqwal'úta elh nzewátet.skan kwa sám7ats.
        # tqílh=k'a án'was t'ánam'ten láti7 kwas wa7 ta=wa7=n-7aw't-ets-cí[t]-ts-as láti7 i=sqwal'út=a elh n-zewát·et-s=kan kwa=sám7a-ts.
        # almost=EPIS two moon at+there.VIS DET+NMLZ+IPFV+TP be DET=IPFV=LOC-behind-mouth-IND-FSGO-TE at+there.VIS PL.DET=speak=EXIS and.then LOC-be.known·FRED-CAUS=FSGS DET+IPFV=white.person-mouth
        # They must have had an interpreter for almost two months before I learned how to speak English.

        # Hal'acítsalem lhun kasts.
        # hal'a-cí[t]-tsalem lhun kas-ts.
        # show-IND-FSG.PASS COMP+IPFV+FSGC how-CAUS
        # They showed me how to use them.

        # O,'' kan tsúnwit, ``Kan ícwa7 eszáyten, xilemlhkán kelh.
        # ``o,'' kan tsún-wit, ``kan ícwa7 es=[s]záyten, xil-em=lhkán=kelh.''
        # oh FSGS say+DIR-TPlo FSGS without have=doings do-MID=FSGS=FUT
        # ``Oh,'' I told them, ``I've got nothing to do, I'll do it.''

        # Kan tsun, ``Kan kw skap'an'tcítsacwa ta nxulák7a?''
        # kan tsun, ``kan kw=s=ka-p'an't-cí[t]-ts-acw-a ta=n-xulák7=a?''
        # FSGS say+DIR whether DET=NMLZ=CIRC-return-IND-FSGO-SSGE-CIRC DET=FSGP-finger=EXIS
        # I asked him, ``Can you put my finger back?''

        # Wa7 múta7 lkw7a ku pála7 wa7 eswátem.
        # ``wa7 múta7 l=kw7a ku=pála7 wa7 es-[s]wátem.''
        # IPFV again at=this.INVIS DET=one IPFV STAT-in.the.way
        # ``There's one more here that is in the way.''

        # T'iqcitsínlhkan kelh múta7 n'án'atcw,'' tsut ku7.
        # ``t'iq-ci[t]-tsín=lhkan=kelh múta7 n'án'atcw,'' tsút=ku7.
        # arrive-IND-SSGO=FSGS=FUT again morning say=QUOT
        # ``I'll bring them to you in the morning,'' he said.

        # Tsícwcitas áku7 ti smúlhatsa áku7 k'emqína.
        # tsícw-cit-as áku7 ti=smúlhats=a áku7 [s]k'em-qín=a.
        # get.there-IND-TE to+there.INVIS DET=woman=EXIS to+there.INVIS edge-top=EXIS
        # He took them to the woman in Sk'emqín.

        # Lánlhkan k'a wa7 kalhaszánucw láti7, zewátenlhkan i wa7 wa7 láti7 álts'q7a.
        # lán=lhkan=k'a wa7 kalhas-[s]zánucw láti7, zewát-en=lhkan i=wa7=wá7 láti7 álts'q7=a, 
        # already=FSGS=EPIS IPFV three-year at+there.VIS be.known-DIR=FSGS PL.DET=IPFV=be at+there.VIS outside=EXIS
        # By the time I was three, I knew about the things outside.

        # Icwa7úllhkan t'u7 láti7 esstám'.
        # icwa7-[7]úl=lhkan=t'u7 láti7 es=stám'.
        # without-real=FSGS=EXCL at+here.VIS have=what
        # I didn't have anything at all.

#   - removed stuff in seg line (and gloss) that was not present in orthographical line
        # Tsúkwkalh aylh láku7, nilh t'u7 aylh múta7 sixin'tsálem ets7á tsal'álha.
        # tsúkw=kalh aylh láku7, nílh=t'u7 aylh múta7 (n)s(a)=six-in'-tsálem e=ts7á tsal'álh=a.
        # finish=FPLS then at+there.INVIS COP=EXCL then again NMLZ=move-DIR-FSG.PASS to=this.VIS Shalalth=EXIS
        # We finished up there, and then they moved me down here to Shalalth.

        # Nilh aylh múta7 sawentúmulem kw snáskalh n7áxwan'em láti7 i sxétqa lt.scúz'sa rep i posta.
        # nilh aylh múta7 s(a)=saw-en-túmulem kw=s=nás=kalh n-7áxw-an'-em láti7 i=sxétq=a l=t=s=cúz'=[s]=a rep i=post=a.
        # COP then again NMLZ=ask-DIR-FPL.PASS DET=NMLZ=go=FPLP LOC-dig-DIR-FPLE at+there.VIS PL.DET=hole=EXIS at=DET=NMLZ=going.to=TP=EXIS stand PL.DET=post=EXIS
        # So then they came and asked us if we wanted to go and dig holes for the pylons.

#   - added missing reduplication boundary (·) to gloss line
        # Lkw7u Missiona lhtsícwas ta nsqátsez7a múta7 i qetsqéqtseksa.
        # l=kw7u Mission=a lh=tsícw=as [ta]=n-sqátsez7=a múta7 i=qets·qé·q·tsek-s=a. 
        # at=that.INVIS Mission=EXIS COMP=get.there=TC DET=FSGP-father=EXIS and PL.DET=TREDolder.brother·CRED·-TP=EXIS
        # My father and his older brothers went to school in Mission.

#   - fixed spacing in gloss line
        # Wa7 t'u7 aylh, nilh ska7a7masása láti7 ta sm'ém'lhatsa láku7.
        # wá7=t'u7 aylh, nilh s=ka-7a·7·ma-s-ás-a láti7 ta=sm'é·m'·lhats=a láku7.
        # IPFV=EXCL then COP NMLZ= CIRC-good·CRED·CAUS-TE-CIRC at+there.INVIS DET=woman·CRED·=EXIS at+there.INVIS
        # So then he fell in love with a girl over there.

#   - kwenswá is glossed 44x with plus signs - here there is a mistake where = is used instead
        # kwenswá ka wa7 ka7áts'xsa, ta ats'xenítasa i srápa.
        # ...kwenswá=ka wa7 ka-7áts'x-s-a, ta=7ats'x-en-ítas=a i=sráp=a.
        # DET=FSGP=NMLZ=IPFV=IRR IPFV CIRC-get.seen-CAUS-CIRC DET=get.seen-DIR-TPle=EXIS PL.DET=tree=EXIS
        # ...if I could see what the trees saw.

#   - xát'em appears 10x as a whole word meaning 'climb', and is never segmented elsewhere.
        # Skéla7s ti7 múta7 kw nsxát'em áku7 éta skela7lhkálha xát'em.
        # [s]=kéla7=s ti7 múta7 kw=n=s=xát'em áku7 e=ta=s=kela7=lhkálh=a xát'-em;
        # NMLZ=first=TP that.VIS and DET=FSGP=NMLZ=climb to+there.INVIS to=DET=NMLZ=first=FPLP=EXIS climb
        # Where we went up at the beginning, that was the first time I'd taken that route;

#   - Two morphemes in the orthog are glossed/segmented as one.
#     The seg/gloss lines have been split for consistency with the orthog line.
#     These two morphemes appeared individually in this combo in other examples, too.
        # Ao7zálh t'u7 láti7 ts'íla ku wa7 qan'im'tsan'tsalítas.
        # ao<7>z'-álh=t'u7 láti7 ts'íla kwa=qan'im'-ts-an'-tsal-ítas.
        # NEG<INCH>-utmost=EXCL at+there.VIS like DET+IPFV=hear-mouth-DIR-FSGO-TPle
        # But it was like there was nobody at all there that understood me.
#   - Similarly, here I edited the seg/gloss to match the sole morpheme present in the orthog line.
        # Nzewátet.stum ku naq'w.
        # n-zewát·et-s-tum kwa=náq'w. 
        # LOC-be.known·FRED-CAUS-FPLE DET+IPFV=steal
        # We learned how to steal.

# - Removed due to missing info we can't fill in (x10)
#   - There is a word (lati7) that is only in the orthog line, not the seg/gloss.
        # Kent7ú cá7a t'it, kénta sqwéqwem'a láti7 s7áw't.sa láti7 ta... stám'as k'á hem' kw snahs i barna? ltsa tsicw p'i7almicwenítas i músmusa, s7áw't.s áku7 lhas ri7p i sq'wéla láti7 – áopv𝚕̲s, tsális, pas, apricots, tákem t'u7.
        # ken=t7ú cá7=a t'it, + ken=ta=sqwé·qw·em'=a láti7 + s-7áw't-s=a ta... + stam'=as=k'á=hem' kw=s-nah-s + i=barn=a? l=tsa + tsicw p'i7-almicw-en-ítas + i=músmus=a s-7áw't-s áku7 lhas ri<7>p i=sq'wél=a láti7: áopv𝚕̲s, tsális, pas, apricots, tákem=t'u7.
        # around=that.VIS high=EXIS also around=DET=mountain·CRED·=EXIS NMLZ-behind-TP to+there.VIS COMP+IPFV+TC grow<INCH> PL.DET=berry=EXIS at+there.VIS apple cherry pear apricots all=EXCL at+there.VIS NMLZ-behind-TP=EXIS DET what=TC=EPIS=ANTI DET=NMLZ-name-TP PL.DET=barn=EXIS at=DET+NMLZ+IPFV+TP+EXIS get.there squeeze-udder-DIR-TPle PL.DET=cow=EXIS
        # Up higher on a hill behind the – what's the name for a barn? – where they went to milk the cows behind there is where the fruit grew: apples, cherries, pears, apricots, everything.
#   - [t] and [s] appear in orthog and seg, but not gloss... 
        # Nilh scuy's ta skalúl7a xexzúmalus aylh, t.stsegtsgalúsemsa t'u7 láti7, aoz kwas katcúsema i kel7ás, nilh tsa t'alhalúsenem éta qwal'ílha.
        # nilh s=cuy'=s ta=skalúl7=a + xe·xzúm-alus aylh, + [t]=[s]=tseg·tsg-alus-em=s=á=t'u7 + láti7, aoz kwas + ka-tcús-em-a i=kel7=ás, + nilh tsa + t'alh-alús-en-em e=ta=qwal'ílh=a.
        # COP NMLZ=going.to=TP DET=owl=EXIS IRED·big-eye then TRED·get.torn-eye-MID=TP=EXIS=EXCL at+there.VIS NEG DET+NMLZ+IPFV+TP CIRC-look-MID-CIRC when[PAST]=first=TC COP DET+NMLZ+IPFV+TP stick-eye-DIR-PASS by=DET=pitch=EXIS
        # From then on the owl has had big eyes, from his eyes being torn open, since he couldn't see at first, because his eyes were stuck together with the pitch. 
#   - morpheme in seg/gloss (second wa7), but not orthog 
        # Nilh iz' wa7 rípin'as i kálitsa, tanápsa, stám'as k'a kwelh nukw slep'cáls.
        # nílh=iz' wa7 ríp-in'-as i=kálits=a, tanáps=a, stám'=as=k'a kwelh=núkw wa7 s-lep'-cál-s.
        # COP=those IPFV grow-DIR-TE PL.INVIS.DET=carrots=EXIS turnip=EXIS what=TC=EPIS PL.DET=other IPFV NMLZ-get.buried-ACT-TP
        # He planted carrots, turnips, a bunch of other stuff.    
#   - word in seg/gloss (ta=wa7/DET=IPFV) that's not in orthog
        # Lhláti7 aylh múta7 lhsúxwastas áku7 na wa7 tsúnem ntakíl'qten.
        # lhláti7 aylh múta7 [lh]=súxwast=as áku7 ta=wá7... na=wa7=tsún-em n-tak-íl'q-ten.
        # from+there.VIS then again COMP=go.downhill=TC to+there.INVIS DET=IPFV ABS.DET=IPFV=say+DIR-FSGE LOC-side-bottom-INS
        # From there it goes down to what we used to call Ntakíl'qten (`bottom of a hill').
#   - morpheme in gloss (to=) that's not in seg/orthog
        # Nilh t'u7 sxlitenítas i plísmena ta ncwelpéka.
        # [nilh]=t'u7 s=xlit-en-ítas i=plísmen=a ta=n-cwelp-ék=a.
        # COP=EXCL NMLZ=get.invited-DIR-TPle PL.DET=policeman=EXIS to=DET=LOC-revolve-back=EXIS
        # Then the policemen called in a helicopter.
#   - this place name (Little Green Place) is glossed as more morphemes than it's segmented as - we suspect that
#     the word green is being reduplicated to create something meaning 'little green place'
        # T'ák.wit, xát'emwit áta7 éta sxál'pta, ts'itemwít éta kwv𝚕̲él'7a.
        # t'ák=wit, xát'em=wit áta7 e=ta=sxál'pt=a, ts'item=wít e=ta=kw𝚕̲·él'·7=a.
        # go.along=TPl climb=TPl to+there.VIS to=DET=Mission.Mountain=EXIS go.towards=TPl to=DET=green·CRED·little.green.place=EXIS
        # They went along, they climbed up Mission Mountain, and then they went towards Kw𝚕̲él'a7 (`Little Green Place').

        # Lhláti7 kwv𝚕̲él'7a lhus t'ák.wit áku7 ta wa7 tsúnem kw𝚕̲i7qs.
        # lhláti7 kwv𝚕̲·él'·7=a lhus t'ák=wit áku7 ta=wa7=tsún-em kw𝚕̲i7-qs.
        # from+there.VIS green·CRED·little.green.place=EXIS COMP+IPFV+TC go.along=TPl to+there.INVIS DET=IPFV=say+DIR-TSG.PASS green-point
        # From the little green place they went to what we call Kw𝚕̲i7qs (`Green point').
#   - word in orthog (nilhsu) segmented as two words
        # Nílhsu tsgánken.
        # ``nílh su tsg-ánk-en.''
        # COP NMLZ+IPFV+SSGP tear-stomach-DIR
        # ``Then you gut it.''
#   - two words in orthog segmented as one word (sk'a... ts'ílas - possibly due to ellipsis)
        # Tcúsem lhláta7 ta míxalha, nilh t'u7 sk'a... ts'ílas ku kaqwéy'a láti7, nilh t'u7 tu7 scúlels.
        # tcús-em lhláta7 ta=míxalh=a, [nilh]=t'u7 s=k'a...=ts'íla=s ku=ka-qwéy'-a láti7, nílh=t'u7=tu7 s=cúlel=s.
        # look-MID from+there.VIS DET=bear=EXIS COP=EXCL NMLZ=EPIS=like=TP DET=CIRC-yelp-CIRC at+there.VIS COP=EXCL=REM NMLZ=run.away=TP
        # The bear looked around, it made a yelping sound, then it just ran away.
#   - word in orthog (nilh) does not appear in seg/gloss
        # T'íqkalh aylh ekw7á lscat'aw'senítas láti7 ta speederha.  Nilh slans láti7 wa7 k'ál'em ta káoha wa7 ambulance.
        # t'íq=kalh aylh e=kw7á l=(t)s=cat'-aw's-en-ítas láti7 ta=speeder=ha, s=lan=s láti7 wa7 k'ál'em ta=káoh=a wa7 ambulance.
        # arrive=FPLS then to=this.INVIS at=NMLZ=take.out-road-DIR-TPle at+there.VIS DET=speeder=EXIS NMLZ=already=TP at+there.VIS IPFV wait DET=car=EXIS IPFV ambulance
        # We got to where they took the speeder off the tracks, and the ambulance was already waiting there.
