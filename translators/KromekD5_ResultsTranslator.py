import os

from translators.translator_functions import write_results


def retrieve_KromekD5_results(filepath):
    """
    Retrieves results from KromekD5 replay tool output in CSV format
    Tested with replay tool PCS Algorithm Offline Tool - version: 170.1.5.7
    For use in RASE, it processes only the first line, as we expect 1 spectrum at a time
    :param filepath: full input file path
    :return: list of (ID, confidence) tuples
    """

    ## Output format:
    ## Label1, Label2, Integration time, Messages(i.e.errors), Result1 confidence, Result1 isotope, Result2 confidence, Result2 isotope, ...

    with open(filepath) as f:
        f.readline()  # skip header line
        line = f.readline()
        results = [s.strip() for s in line.split(',')[4:]]
    return list(zip(results[1::2], results[0::2]))


def main(input_dir, output_dir):
    in_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for fname in in_files:
        ResultsArray = retrieve_KromekD5_results(os.path.join(input_dir, fname))
        new_fname = os.path.join(output_dir, fname[:-4] + '.n42')
        write_results(ResultsArray, os.path.join(output_dir, new_fname))
    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
