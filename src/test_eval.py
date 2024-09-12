import click
import pandas as pd

EXPECTED_RESULT_NULL_MARKER = "None"

def check_results(outputted_results, expected_results):
    header = list(outputted_results)
    assert(len(header) == len(expected_results))
    for index, col_name in enumerate(header):
        outputted_result = outputted_results.iloc[0][col_name]
        expected_result = expected_results[index]
        if (outputted_result == expected_result) or (pd.isnull(outputted_result) and expected_result == EXPECTED_RESULT_NULL_MARKER):
            pass
        else:
            print(f"\nIncorrect evaluation result for {col_name}.\nExpected {expected_result}, but got {outputted_result}.")

@click.command()
@click.option("--results_csv", required=True, help="The path to the CSV where the eval results are being printed.")
@click.option("--expected_results", required=True, help="A string representing the row of eval results we expect for the test data.")
def main(results_csv, expected_results):
    print("\nChecking evaluation results...")
    current_results = (pd.read_csv(results_csv)).tail(1)
    check_results(current_results, expected_results.split(","))

main()