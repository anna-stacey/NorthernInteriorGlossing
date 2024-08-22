import click
from glossed_data_utilities import read_file

OOL_MARKER = "*"

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
        total_sentences = len(predictions_1)
        diff_sentences = 0
        total_words = 0
        diff_words = 0
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
                word_counts = _print_discrepancies(sentence_1, sentence_2, 1)
                total_words +=  word_counts[0]
                diff_words +=  word_counts[1]
                diff_sentences += 1
            elif check_gloss_line and (sentence_1[2] != sentence_2[2]):
                print("\n\n\nDiscrepancy in gloss line:")
                _print_sentences(file_1, file_2, sentence_1, sentence_2)
                word_counts = _print_discrepancies(sentence_1, sentence_2, 2)
                total_words +=  word_counts[0]
                diff_words +=  word_counts[1]
                diff_sentences += 1
            else: # No relevant problems!
                # Ignore OOL words
                total_words += len(sentence_1[1].split(" ")) - sentence_1[1].count("*")

        print(f"\n\n{diff_sentences}/{total_sentences} sentences with discrepancies.")
        print(f"{diff_words}/{total_words} mispredicted words.")
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

def _print_discrepancies(sentence_1, sentence_2, line_number_under_consideration):
    total_words = 0
    diff_words = 0
    print("\nDiffering words:")
    for word_1, word_2 in zip(sentence_1[line_number_under_consideration].split(" "), sentence_2[line_number_under_consideration].split(" ")):
        assert(word_1.startswith(OOL_MARKER) == word_2.startswith(OOL_MARKER))
        if not word_1.startswith(OOL_MARKER):
            total_words += 1
            if word_1 != word_2:
                diff_words += 1
                print("\t-", word_1, "vs", word_2)

    return total_words, diff_words

main()
