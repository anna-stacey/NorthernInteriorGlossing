from os import getcwd, walk
from split_dataset import create_file_of_sentences, read_file

# Returns a train, dev, and test dataset
def create_datasets():
    stories = [None] * 18
    current_story = []
    folder_path = "/Data/statimcets/"

    # We want to read in the sentences while maintaning the story structure,
    # so that we can divide the data up by story
    for root, dirs, files in walk(getcwd() + folder_path):
        for file_name in files:
            if file_name.startswith("story") and file_name.endswith(".txt"):

                # Read in all the sentences
                current_story.extend(read_file(getcwd() + folder_path + file_name)[:])
                
                # Get the story number so we know which story this is
                # (It doesn't read the stories in order so we need to order them manually)
                file_number = int(file_name[6:-4]) - 1

                # Insert the story at the correct numerical pos in our list of stories
                stories.pop(file_number)
                stories.insert(file_number, current_story)

                # Reset
                current_story = []

    for i, story in enumerate(stories):
        print(f"Story #{i + 1} has {len(story)} sentences.")

    # Total amount of sentences in the data = 977
    # The breakdown by story is as follows:
    # story 1: 114
    # story 2: 53
    # story 3: 24
    # story 4: 73
    # story 5: 59
    # story 6: 25
    # story 7: 52
    # story 8: 32
    # story 9: 46
    # story 10: 67
    # story 11: 37
    # story 12: 66
    # story 13: 30
    # story 14: 16
    # story 15: 74
    # story 16: 79
    # story 17: 47
    # story 18: 83
    # We want a 60%/20%/20% train/dev/test split
    # Train goal: 586 sentences, 11 stories
    # Dev goal: 195 sentences, 4 stories
    # Test goal: 195 sentences, 4 stories
    # DEV: Stories 17, 18, 11, 6 = 192 sentences, 4 stories
    # TEST: Stories 2, 3, 4, 9 = 196 sentences, 4 stories
    # TRAIN: the rest of the stories = 589 sentences, 10 stories

    # Assemble the stories into the three sets
    train, dev, test = [], [], []
    train.extend([stories[0]])
    train.extend([stories[4]])
    train.extend(stories[6:8])
    train.extend([stories[9]])
    train.extend(stories[11:16])
    sentence_count = 0
    for story in train:
        sentence_count += len(story)
    print("Train data:", len(train), "stories containing", sentence_count, "sentences.")
    
    dev = [stories[5]] + [stories[10]] + stories[16:]
    sentence_count = 0
    for story in dev:
        sentence_count += len(story)
    print("Dev data:", len(dev), "stories containing", sentence_count, "sentences.")
    
    test = stories[1:4] + [stories[8]]
    test_sentence_count = 0
    for story in test:
        test_sentence_count += len(story)
    print("Test data:", len(test), "stories containing", test_sentence_count, "sentences.")

    return train, dev, test

# Converts from a list of stories to just a list of examples, then calls create_file_of_sentences
def create_file_of_sentences_helper(list, file_name):
    list_of_sentences = []
    for story in list:
        list_of_sentences.extend(story)
    create_file_of_sentences(list_of_sentences, file_name)

def main():
    # Read the files and break them down into the three sets
    train, dev, test = create_datasets()
    create_file_of_sentences_helper(train, "train.txt")
    create_file_of_sentences_helper(dev, "dev.txt")
    create_file_of_sentences_helper(test, "test.txt")

if __name__ == '__main__':
    main()
