# *** Common functions for creating train/dev/tests datasets ***
from os import getcwd, mkdir, path
from re import sub

NON_PERMITTED_PUNCTUATION = [".", ",", "?", "\""]

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
                for punctuation in NON_PERMITTED_PUNCTUATION:
                    line = line.replace(punctuation, "")

            # Find 2+ spaces, and replace them with only one space
            line = sub(r"[ ]+[ ]+", " ", line)

            updated_sentence.append(line)
        updated_dataset.append(updated_sentence)
        updated_sentence = []

    return updated_dataset

def create_file_of_sentences(examples, file_name):
    output_folder = "/data/"

    # Create the generated_data subdirectory, if it doesn't already exist
    dir_path = getcwd() + output_folder
    if not path.exists(dir_path):
        mkdir(dir_path)

    write_sentences(examples, dir_path + file_name)

# Assumes that lines do NOT end in "\n", and will add it as it prints
def write_sentences(examples, file_path):
    with open(file_path, "w") as file:
        for i, example in enumerate(examples):
            if len(example) > 0:
                for j, line in enumerate(example):
                    file.write(line + "\n")
                    # Add blank line after each example (but not if it's the end of the dataset, bc that results in a double newline at EOF)
                    if (j >= len(example) - 1) and (i < len(examples) - 1):
                        file.write("\n")
        file.close()
