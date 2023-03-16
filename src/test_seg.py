import click

# Returns a list of lines in the file, "\n" within the line removed
def read_file(file_path):
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

@click.command()
@click.option("--output_file", help="The name of the output file.")
@click.option("--gold_output_file", help="The name of the gold output file.")
def main(output_file, gold_output_file):
    print("Comparing these files:", output_file, gold_output_file)
    
    # Get the test results
    output = read_file(output_file)
    output = format_fairseq_output(output)

    # Get the gold labels
    gold_output = read_file(gold_output_file)
    
    # Compare!
    evaluate(output, gold_output)

# Doing this so that I can export functions to pipeline.py
if __name__ == '__main__':
    main()
