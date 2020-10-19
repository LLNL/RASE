.. _workflowStep6:

*************************************************************
RASE Workflow Step 6: Replay Tool Results Analysis
*************************************************************

View Results
============

The “View Results” button will display the table with a summary of the replay tool results for the selected instrument
and scenario combination. If multiple scenario/instrument combinations are selected, the results button will remain clickable so long as
at least one instrument/scenario combination in the selected instruments/scenarios has results that are ready to be viewed.
The number of columns displayed in the view results dialog can be customized via the table settings dialog, using the "Table Settings" button.
The user may also freely modify the correspondence table using the "Correspondence Table" button, which will update the results table live.
If a material name is in the format of XXnnn (e.g.: Rn226, K40) and the material is set as a source material, RASE will automatically look for
"XX-nnn" as well as "XXnnn" when calculating the results (so if Cs137 was defined as a material, RASE would consider an identification of
Cs-137 and Cs137 as "correct IDs"). This is not done when a material of this format is defined in the background (so Cs137 and Cs-137 are
considered as two separate identifications). For background materials, the equivalence must be enforced manually and on an isotope-by-isotope
basis in the correspondence table.

Detailed identification results for each individual spectrum can be reviewed by clicking on the scenario title in the
first column of the "View Results" table. Detailed identification results are useful to identify spectra that provided unexpected results or to determine how to adjust the correspondence table comprehensions to better match the objectives of a specific study.
Use Ctrl+C or right-click to copy the ID results and use the exact entries to modify the correspondence table comprehensions.

The tables in the "View Results" and "Detailed Results" dialogs can be exported as a \*.csv file and processed in Excel for plotting and extended analysis. The RASE-generated sampled spectra and replay tool outputs can be reviewed manually using programs like PeakEasy and Interspec.

.. _rase-WorkflowStep6a:

.. figure:: _static/rase_WorkflowStep6.png
    :scale: 75%

    Main RASE window showing how to access identification results dialogs



.. figure:: _static/rase_WorkflowStep6-2.png
    :scale: 75%

    “View Results” and "Detailed Results" tables.

|

RASE uses the unweighted F-Score methodology based on the geometric mean of precision and recall to evaluate the identification
performance of an algorithm. For more details on the F-Score see [AIP]_.

Confidence intervals in RASE are are determined using the Wilson Score approach. Wilson Score intervals are biased
towards 0.5, and are asymmetric, but have been shown to have a more accurate performance than "exact" methods such as
Clopper-Pearson, which tend to be overly conservative (see Newcombe, 1998).

Each term in the view results table is calculated independently for each sample spectrum, and then averaged across
all replications for a given scenario. The information in the columns are defined as follows:

.. math::
   Prob_{\text{ID}} = \begin{cases}
                        1, & \text{if all isotopes are correctly identified}\\
                        0, & \text{otherwise}
                      \end{cases}
.. math::
   {\text{CIs (for both } Prob_{\text{ID}} \text{ and } C\&C)} = {\text{Upper and lower confidence interval bounds for a given } \alpha}
.. math::
   {\text{True Positives}} = \frac{\text{# of true positives}}{\text{total # of sources in scenario}}
.. math::
   {\text{False Positives}} = {\text{Number of identified isotopes that were not defined in the scenario sources}}
.. math::
   {\text{False Negatives}} = {\text{Number of isotopes defined in the scenario sources that were not identified}}
.. math::
   C\&C {\text{ (Complete \& Correct)}} = \begin{cases}
                                        1, & \text{if all sources are correctly ID'd with no false positives}\\
                                        0, & \text{otherwise}
                                        \end{cases}
.. math::
   Precision = \frac{\text{# of true positives}}{\text{(# of true positives) + (# of false positives)}}
.. math::
   Recall = \frac{\text{# of true positives}}{\text{(# of true positives) + (# of false negatives)}}
.. math::
   F_{\text{Score}} = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision + Recall}}


Plotting
========

RASE includes built-in 2D plotting capabilities. Using the drop-down selection boxes in the bottom left of the "View Results" window, the user may select any of the possible results columns as x and y axes to plot against each other. If the user chooses source/background dose/flux as one of the axes, they will be prompted to choose one of the source/background isotopes to plot. The "Category" option allows the user to further break up results into several relevant groups. For example, the user may choose "Detector" as a category for plotting pID vs Source Dose; if there are results for more than one detector in the results table, the results for these two detectors will be plotted in different colors on the same plot. Clicking "View Plot" will bring up a plotting dialog displaying the selected data.

The plotting capabilities are particularly specialized for S-curve fitting. In the plotting dialog the user may select which dataset to fit curves to (if categories are defined), specify confidence intervals for the fit (to help convergence in certain cases), and set a percent for ID threshold estimation. Pressing "Plot S-Curve" will fit a sigmoid trendline, if possible. The fit is done using a linear or a log-spaced Boltzmann Sigmoid function, as specified by the user, using the equation:

.. math::
   y_{Fit} = a_2 + \frac{a_1 - a_2}{1 + Q e^{-Bx}} \quad {\text{or}} \quad y_{Fit} = a_2 + \frac{a_1 - a_2}{1 + Q e^{-B \,\times\, ln(x)}}


This plot works for curves where the identification rate is positively correlated with source intensity as well as negatively correlated. If the fit is successful, the S-curve is plotted with a 1-sigma confidence interval surrounding the line and a point is marked on the plot where the trendline crosses an ID threshold (default is 80%, but can be varied by the user). The x-value of this crossing point is noted in the legend. These graphical features can be toggled on or off. The user may also select the uncertainty to provide the fitting algorithm, which may help convergence in certain cases. Detailed fit results are displayed in the window to the left regardless of if the fit was successful. This can be toggled on or off Various properties of the plot, including title and axes scale/labels, can be modified by the user. The plot can be exported in the user's favorite image file format.



.. _rase-WorkflowStep6b:

.. figure:: _static/rase_WorkflowStep6-3.png
    :scale: 80%

    “View Results” table and "Plotting" window.
