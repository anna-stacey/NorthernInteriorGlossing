import click
from glossed_data_utilities import read_file

@click.command()
@click.option("--file_1", help = "The name of the first pred file.")
@click.option("--file_2", help = "The name of the second pred file.")
def main(file_1, file_2):
    predictions_1 = read_file(file_1)
    predictions_2 = read_file(file_2)

    assert(len(predictions_1) == len(predictions_2))
    diff_sentences = 0
    for sentence_1, sentence_2 in zip(predictions_1, predictions_2):
        if sentence_1[1] != sentence_2[1]:
            print("\n\n\n")
            print(file_1 + ":")
            for line in sentence_1:
                print(line)

            print()
            print(file_2 + ":")
            for line in sentence_2:
                print(line)
            diff_sentences += 1

    print(f"\n\n{diff_sentences} sentences with discrepancies.")

main()
