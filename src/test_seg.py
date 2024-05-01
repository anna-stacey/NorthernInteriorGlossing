import click
from gloss import make_sentence_list_with_prediction
from glossed_data_utilities import read_file, write_sentences, OUT_OF_LANGUAGE_MARKER

# Returns a list of lines in the file, "\n" within the line removed
def read_lines_from_file(file_path):
    with open(file_path) as f:
        lines = f.readlines()

    formatted_lines = []
    for line in lines:
        line = line.replace("\n", "")
        formatted_lines.append(line)

    return formatted_lines

# Given the output from running fairseq on the test data, get just the actual output
def format_fairseq_output(output):
    formatted_output = []
    # First, just grab all the H-X lines
    for line in output:
        if line.startswith("H-"):
            # The actual word comes after two tabs
            word = line.split("\t")[2]
            formatted_output.append(word)

    return formatted_output

# No return value
# Evaluate the accuracy word by word
def evaluate(output, gold_output):
    assert(len(output) == len(gold_output))
    seg_count = 0
    incorrect_seg_count = 0
    for output_seg, gold_seg in zip(output, gold_output):
        if output_seg != gold_seg:
            incorrect_seg_count += 1
        seg_count += 1

    assert(seg_count > 0)
    accuracy = (seg_count - incorrect_seg_count) / seg_count
    accuracy = round(accuracy * 100, 2)
    print(f"Accuracy: {accuracy}% on {seg_count} words.")

def reassemble_predicted_line(entire_input, predicted_seg_word_list):
    predicted_seg_line_list = []
    current_word_index = 0
    # Go through each input sentence and count the number of words.
    # Then grab that many words from our long list of predicted words, and that will be our prediction line.
    # But also, add back in words marked as OOL.
    for input_sentence in entire_input:
        predicted_seg_line = []
        line_word_count = len(input_sentence[0].split()) - input_sentence[0].count(OUT_OF_LANGUAGE_MARKER)
        # Grab the predicted words
        predicted_seg_line.extend(predicted_seg_word_list[current_word_index : current_word_index + line_word_count])
        # Get rid of s p a c e s between letters
        predicted_seg_line = [word.replace(" ", "") for word in predicted_seg_line]
        # Add back any asterisk-marked words
        for index, input_word in enumerate(input_sentence[0].split()):
            if input_word.startswith(OUT_OF_LANGUAGE_MARKER):
                predicted_seg_line.insert(index, input_word)

        predicted_seg_line = " ".join(predicted_seg_line)
        # Update our progress through the predicted word list
        current_word_index += line_word_count
        predicted_seg_line_list.append(predicted_seg_line)

    return predicted_seg_line_list

@click.command()
@click.option("--whole_input_file", help="The name of the input file (i.e., with the transcription, seg, gloss, etc.).")
@click.option("--output_file", help="The name of the output file.")
@click.option("--gold_output_file", help="The name of the gold output file.")
def main(whole_input_file, output_file, gold_output_file):
    print("Comparing these files:", output_file, gold_output_file)
    
    # Get the test results
    output = read_lines_from_file(output_file)
    output = format_fairseq_output(output)

    # Get the gold labels
    gold_output = read_lines_from_file(gold_output_file)
    
    # Compare!
    evaluate(output, gold_output)

    # Print a viewable output
    # First read in and print out the gold
    entire_input = read_file(whole_input_file)
    write_sentences(entire_input, "generated_data/seg_gold.txt")
    # Now format and print a version with our predictions
    formatted_output = reassemble_predicted_line(entire_input, output)
    sentences_with_predictions = make_sentence_list_with_prediction(entire_input, formatted_output, 1)
    write_sentences(sentences_with_predictions, "generated_data/seg_pred.txt")
# Doing this so that I can export functions to pipeline.py
if __name__ == '__main__':
    main()
