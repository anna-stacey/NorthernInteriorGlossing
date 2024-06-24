import click
from glossed_data_utilities import read_file

@click.command()
@click.option("--check_seg_line", is_flag = True, help = "Should the seg line be checked for discrepancies?")
@click.option("--check_gloss_line", is_flag = True, help = "Should the gloss line be checked for discrepancies?")
@click.option("--file_1", help = "The name of the first pred file.")
@click.option("--file_2", help = "The name of the second pred file.")
def main(check_seg_line, check_gloss_line, file_1, file_2):
    if check_seg_line or check_gloss_line:
        predictions_1 = read_file(file_1)
        predictions_2 = read_file(file_2)

        assert(len(predictions_1) == len(predictions_2))
        diff_sentences = 0
        for sentence_1, sentence_2 in zip(predictions_1, predictions_2):
            # If there's a discrepancy in *both* lines, just print once
            if check_seg_line and check_gloss_line and (sentence_1[1] != sentence_2[1]) and (sentence_1[2] != sentence_2[2]):
                print("\n\n\nDiscrepancy in segmentation AND gloss lines:")
                _print_sentences(file_1, file_2, sentence_1, sentence_2)
                diff_sentences += 1
            # Otherwise, check the seg and gloss lines individually
            elif check_seg_line and (sentence_1[1] != sentence_2[1]):
                print("\n\n\nDiscrepancy in segmentation line:")
                _print_sentences(file_1, file_2, sentence_1, sentence_2)
                diff_sentences += 1
            elif check_gloss_line and (sentence_1[2] != sentence_2[2]):
                print("\n\n\nDiscrepancy in gloss line:")
                _print_sentences(file_1, file_2, sentence_1, sentence_2)
                diff_sentences += 1

        print(f"\n\n{diff_sentences} sentences with discrepancies.")

    else:
        print("\nERROR: Please specifiy a line to check for discrepancies (check out command line arg help for more info).")

def _print_sentences(file_1, file_2, sentence_1, sentence_2):
    print(file_1 + ":")
    for line in sentence_1:
        print(line)

    print()
    print(file_2 + ":")
    for line in sentence_2:
        print(line)

main()
