from os import getcwd, walk
from split_dataset import read_file

def assemble_datasets():
    sentence_sets = []
    folder_path = "/data/nle?kepmxcin/"
    for root, dirs, files in walk(getcwd() + folder_path):
        for file in files:
            sentence_sets.append(read_file(getcwd() + folder_path + file)[:])

    print_data_summary(sentence_sets)
    
# Takes a list of sentence sets, each of which contains a list of sentences
def print_data_summary(sentence_sets):
    print(f"There are {len(sentence_sets)} different files of sentences.")
    
    total_sentence_count = 0
    for i, sentence_set in enumerate(sentence_sets):
        print(f"File {i} has {len(sentence_set)} sentences.")
        total_sentence_count += len(sentence_set)

    print(f"There are {total_sentence_count} total sentences.")

def main():
    assemble_datasets()

if __name__ == '__main__':
    main()
