.. _dynamic_output:

********************************
Interpreting Dynamic RASE Output
********************************

Each test specified in the Dynamic RASE YAML configuration will produce output according to the ``operations`` block in the configuration. The output is printed to the console and can also be saved as a CSV table if a ``csv_output`` field is provided in the configuration specifying a file path.

In the output table, columns for each test's name, sources, and replications are always available.

If the operation ``evaluate_detection`` is provided (which generally requires the operations ``output_files``, ``replay_files``, ``translate_replay``, and ``evaluate_detection`` to be performed either in the same configuration or in previous configurations) a column labelled "Prob. of Detection" will be output. This indicates the number of replications in which the replay tool's output included a detection of the value specified in the ``replay_name`` parameter in the scenario for this test.

If the operation ``print_scores`` is provided, one column is output for each scorer and each source among all tests (as each source receives its own score). The meaning of these scores is specific to each scorer.

If the operation ``show_plots`` is provided, plots are displayed according to the ``plots`` block in the configuration. These plots are useful for visualizing the behavior of the models trained for the tests.
