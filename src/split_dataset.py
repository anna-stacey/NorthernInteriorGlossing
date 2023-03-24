from os import getcwd, walk

# Returns a train, dev, and test dataset
def create_datasets():
    speaker_1_folder_path = "/plaintext/BS/"
    speaker_1_sentences = read_all_files_for_speaker(speaker_1_folder_path)
    print(f"Speaker 1: {len(speaker_1_sentences)} sentences.")

    speaker_2_folder_path = "/plaintext/HH/"
    speaker_2_sentences = read_all_files_for_speaker(speaker_2_folder_path)
    print(f"Speaker 2: {len(speaker_2_sentences)} sentences.")

    speaker_3_folder_path = "/plaintext/VG/"
    speaker_3_sentences = read_all_files_for_speaker(speaker_3_folder_path)
    print(f"Speaker 3: {len(speaker_3_sentences)} sentences.")

    # Total amount of sentences in the data = 1294
    # Because speaker 2 has the least data available, that will be our test set
    # Training set is then speaker 1 + speaker 3 = 924
    # We want ~20% for dev = 185 sentences
    # Probably best to group data by story (more realistic?), so we'll find a story cutoff close to that
    # Dev data = last six stories from speaker 3 (starts from sentence 299)

    train = speaker_1_sentences + speaker_3_sentences[:298]
    print("Train data:", len(train), "sentences.")
    dev = speaker_3_sentences[298:]
    print("Dev data:", len(dev), "sentences.")
    test = speaker_2_sentences
    print("Test data:", len(test), "sentences.")

    return train, dev, test

# Read in each file from this speaker, and return all the example sentences stored in one big list
def read_all_files_for_speaker(folder_path):
    sentences = []
    for root, dirs, files in walk(getcwd() + folder_path):
        for file in files:
            if file.endswith(".txt"):
                sentences.extend(read_file(getcwd() + folder_path + file)[:])
          
    return sentences

# Returns a list of examples (where each example is a list containing the 5 lines)
def read_file(file_path):
    with open(file_path) as f:
        lines = f.readlines()
        lines.append("\n") # So that the final sentence also ends in a blank line

    sentences = []
    current_sentence = []
    for i, line in enumerate(lines):
        if (i + 1) % 6 == 0: # Every 6th line is a blank line marking the end of the current sentence
            sentences.append(current_sentence)
            current_sentence = []
        else:
            current_sentence.append(line)
    # The final sentence needs to end with a newline, for consistency
    sentences[-1][-1] = sentences[-1][-1] + "\n"
    return(sentences)

def create_file_of_sentences(list, file_name):
    file = open(file_name, "w")
    for example in list:
        if len(example) > 0:
            for i, line in enumerate(example):
                file.write(line)
                if i >= len(example) - 1: # Final line
                    file.write("\n")
    file.close()

def main():
    # Read the files and break them down into the three sets
    train, dev, test = create_datasets()
    create_file_of_sentences(train, "train.txt")
    create_file_of_sentences(dev, "dev.txt")
    create_file_of_sentences(test, "test.txt")

main()
