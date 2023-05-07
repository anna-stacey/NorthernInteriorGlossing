# *** Common functions for creating train/dev/tests datasets ***

# Returns a list of examples (where each example is a list containing the transcription, seg, etc. lines)
def read_file(file_path, lines_per_example):
    with open(file_path) as f:
        lines = f.readlines()
        # To handle inconsistencies in file formatting - add a new line if the file doesn't already end in one 
        if not lines[-1].endswith("\n"):
            # The new line ensures the final example can processed in the same way as all the previous examples
            lines[-1] = lines[-1] + "\n"
        # Add this regardless, bc readlines() doesn't seem to read in the newline at EOF
        lines.append("\n")

    sentences = []
    current_sentence = []
    for i, line in enumerate(lines):
         # After each example is a blank line marking the end of the current sentence
         # Whenever we get there, it's time to add the present example to our list
        if (i + 1) % (lines_per_example + 1) == 0:
            sentences.append(current_sentence)
            current_sentence = []
        else:
            current_sentence.append(line)

    return(sentences)

def create_file_of_sentences(list, file_name):
    file = open(file_name, "w")
    for i, example in enumerate(list):
        if len(example) > 0:
            for j, line in enumerate(example):
                file.write(line)
                # Add blank line after each example (but not if it's the end of the dataset, bc that results in a double newline at EOF)
                if (j >= len(example) - 1) and (i < len(list) - 1):
                    file.write("\n")
    file.close()
    