from os import getcwd, walk
from split_dataset import create_file_of_sentences, read_file

# Returns a train, dev, and test dataset
def create_datasets():
    base_path = "/Data/gitksan/"
    speaker_1_folder_path = base_path + "BS/"
    speaker_1_sentences = read_all_files_for_speaker(speaker_1_folder_path)
    print(f"Speaker 1: {len(speaker_1_sentences)} sentences.")

    speaker_2_folder_path = base_path + "HH/"
    speaker_2_sentences = read_all_files_for_speaker(speaker_2_folder_path)
    print(f"Speaker 2: {len(speaker_2_sentences)} sentences.")

    speaker_3_folder_path = base_path + "VG/"
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

    print("Finished splitting the three datasets.")
    return train, dev, test

# Read in each file from this speaker, and return all the example sentences stored in one big list
def read_all_files_for_speaker(folder_path):
    lines_per_example = 5
    sentences = []
    for root, dirs, files in walk(getcwd() + folder_path):
        for file in files:
            if file.endswith(".txt"):
                sentences.extend(read_file(getcwd() + folder_path + file, lines_per_example)[:])
          
    return sentences

def main():
    # Read the files and break them down into the three sets
    train, dev, test = create_datasets()
    create_file_of_sentences(train, "train.txt")
    create_file_of_sentences(dev, "dev.txt")
    create_file_of_sentences(test, "test.txt")

if __name__ == '__main__':
    main()
