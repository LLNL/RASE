.. _dynamic_models:

****************************************
Models and Keywords Used in Dynamic RASE
****************************************

Dynamic RASE utilizes many keywords throughout its operation.

Scenario Paths Type Keywords
============================

Each scenario block should specify a :code:`path`, which describes the relative motion of the sources and the detector.

A :code:`path` block, at a minimum, specifies a :code:`path_type`. Available options for :code:`path_type` are:

StayPutPath
-----------
This path describes a non-moving source.
It takes a single extra parameter, :code:`pos`, describing the position where the source will remain during the entire scenario.

OneStepPath
-----------
This path describes a source which begins at a particular position :code:`firstpos` and at :code:`switchtime` teleports to :code:`secondpos`.

NStepPath
---------
This path describes a source that begins at one position at time = 0 and then, at `N` later times, moves instantly to the next of `N` additional positions.

It takes a parameter :code:`times`, a list of length `N`, and a parameter :code:`pos`, a list of length `N` + 1 (including the first position).

InMotionPath
------------
This path describes continuous motion between points. As with NStepPath, it takes a list of `N` + 1 positions and `N` times. However, at times in between the specified times the source position is linearly interpolated between the specified points.

This path should be used for cases of simple continuous motion between two points, providing the stop and start points as a two-element list for :code:`pos` and the stop time as a one-element list for :code:`times`.



Spatial Models
==============

Each test in the :code:`tests` block should specify a :code:`model`, choosing from one of several models available in Dynamic RASE.

Each test should also provide a :code:`model_def` block containing parameters specific to the model.

Available model types are:

RecreateModel
-------------
This model "re-creates" the input data exactly. If queried at a location where there is input data, the model returns the spectral shape and intensity of that input data. If queried at any other location, the model fails with an error.

This model is useful for validation of Dynamic RASE's other models against existing data. It works well with NStepPath, but does not work with InMotionPath, as that path type requires the ability to interpolate between input data points.

This model should be provided with a :code:`model_def` consisting of::

    model_def: ["N/A",]

ManyGPsModel
------------
This model uses a Gaussian process (GP) approach to interpolation between the input data. Many GPs are used, one per
energy bin in the input sp-ectra.

This model has an optional ``points`` parameter, a list of input data locations to use as training points for the GPs. These must be positions available from the input data provided. If no ``points`` parameter is provided, the model will use all locations available in the input data.

ManyGPsROIModel
---------------
This model is similar to the ManyGPsModel, but requires an ``roi`` parameter. This ``roi`` parameter may either provide a list of energy bins, or sub-parameters ``first`` and ``last`` to specify a range of energy bins. These energy bins will be modeled using GPs, while all other energy bins will be modeled as fixed at zero counts.

Use of this model type is recommended, as specifying an ROI will reduce the time spent training GPs in uninteresting energy bins.

ProxyModel
----------
This is an extension of the ManyGPsROIModel that uses one or more sources with many input data locations as a "proxy" for a "target" source with only one input data location available. This is useful for users with plentiful data taken with a common laboratory source who would like to approximate an unusual source for which a full multi-location measurement campaign is impractical.

For each "target" source, the model will use the one location available in the input data (or the nearest, if the user provides more than one input data locations) as an "anchor" providing the spectral shape of the target.

Next, the model will look at the ``proxies`` block in the ``model_def``. Each of these proxies should provide a source name, an ``roi``, and a ``weight``. The proxy sources will be combined proportionally according to the normalized weights and used to determine the relationship between source location and bin-by-bin measurement intensity.

This relationship is combined with the spectral shape of the "anchor" to extrapolate the behavior of the target source at other locations.

The ProxyModel is an approximation and should only be used when multi-location data is not available for the target source.

SymmetricMGRModel
-----------------
This model is another extension of the ManyGPsROIModel. It uses a specialized kernel that enforces symmetry around an axis provided by a ``reflection_axis`` parameter, which should be provided as a list of [x,y,z] coordinates.

Scoring Models
==============

Only a few relatively basic scorers are currently implemented in Dynamic RASE. The scoring system is designed to be extensible and more sophisticated scorers can be included by the developers if desirable approaches to comparing model versus true spectra are proposed.

The currently implemented scoring models require that the points at which scores are requested have base spectra at that point to use as a basis for comparison. To get a good idea of the models, it may be a good idea to leave one or more training points out of the model definition such that scoring is not done on training points, giving an overly optimistic performance evaluation. This is not ideal if collected data is sparse and every point has great significance; in this case, one possible approach would be to define several tests using the same scenario and model but leave a single, different training point out each time. Scoring can then be done on that excluded point for each model, giving an overall idea of how stable the model is when using all the points as well as how important each point is for smooth and accurate simulation.


ScoreMaxDifference
------------------
This scorer returns the single largest difference between any bin in the model and any of the input data for the source, among all provided locations.

This single largest difference will generally be at a spectra peak and at the closest location, as this results in the greatest counts in the input spectrum and therefore offers the largest difference in a well-functioning model. This can be reasonably predictive of source detection behavior, as detecting a source is greatly influenced by spectral peaks and the behavior at the closest approach, but this predictive relationship is very approximate.

ScoreMaxDifferenceDivTotalCounts
--------------------------------
This scorer divides the maximum difference between input and model across all energy bins by the total counts in the input spectra at each location. The greatest difference / total counts ratio across all locations is the resulting score.

This approach, unlike ScoreMaxDifference, does is not primarily determined by discrepancies at the point of closest approach. As a result, it may be useful in scenarios where it is especially important that the model be accurate over the entire field.

ScoreMaxDifferenceAcrossROI
---------------------------
This scorer takes an ``roi`` parameter with ``first`` and ``last`` sub-parameters to provide a range of energy bins over which the scorer looks. It otherwise behaves like ScoreMaxDifference.

Plotting Models
===============

There are several options for plotting a simulation. The user can choose to plot things in 3D, where a detector response map for a bin (or bins) of interest will be plotted, or in 2D, where the detector response map along a linear path will be plotted. The different possible plotting models are noted here. Note that the user can assign multiple plotter models to the same spectrum. Dynamic RASE does not check to make sure that all models defined for a plot are compatible, so the user should take care to make sure that the models being defined together are sensible.


plot_3D_model
-------------

This model simply plots the 3D detector response surface across all space. This map is currently only capable of plotting the detector response map across the X-Y plane, with the Z axis indicating the intensity of the response. This model is selected by setting the ``dimensions`` keyword to 3 and defining this model as one of the members of the ``plotter`` keyword list. The user can choose to either plot the detector response map in real space or in 1/r^2 adjusted "model" space, but using the words `real` or `model` for the ``plot_type`` keyword. The user then defines a list of tests for the ``test`` keyword. Each test defined here will create a different plot. The user can define limits for the plots using the ``limits`` keyword, which has the sub-keywords of ``X``, ``Y`` and ``Z``. Each of these keywords expects a 2-element list. If not included, the plots default to X = [-301, 301] and Y = [29, 301]. In the current implementation of Dynamic RASE, the ``Z`` component is ignored but should still be defined as a list of 2 numbers. Finally, the user can plot one or more bins by defining a list for the ``bin`` keyword. As with the tests, each bin will create a uniquely generated plot.

plot_3D_train
-------------

This model plots training points in 3D. If the user would like to visualize the training data or the test data without the detector response map, this is the model to use. Alternatively, the "plot_3D_model" and "plot_3D_points" can be plotted together to visualize the detector response and the training points used to create that response. This model uses all the same keywords as "plot_3D_model", with the added keyword ``plot_error``. The ``plot_error`` keyword can either take a True or False. If the keyword is not specified or nothing is provided here it defaults to False.

plot_3D_train_colored_by_model
------------------------------

This model is the same as plot_3D_train and takes all the same keywords. The only difference is that this model also gives the points unique coloration and symbols depending on where it lies relative to the detector response map. If the value of the points are within 5% of the response map, they will be green circles, regardless of if they are above or below the response map. If they are further than 5% away, they will be blue circles (if less than the map) or red circles (if greater). If the difference is greater than 20%, the symbols are triangles (with the same coloration as for the 5%-20% case), and if greater than 50% they are squares (again with the same coloration). The user should choose to either use "plot_3D_train" or "plot_3D_train_colored_by_model", not both.

plot_3D_test/plot_3D_test_colored_by_model
-------------------------------------------

These models are identical to the two models above in terms of functionality. The difference is that these models plot test data, not training data. The test data selected to plot is defined using the ``scorer`` keyword. This keyword expects only a single value: the name of a scorer from which to source test points. This keyword is mandatory if using either of these two models. The user is free to use the "plot_3D_model", "plot_3D_train"/"plot_3D_train_colored_by_model", and "plot_3D_test"/"plot_3D_test_colored_by_model" together in a single plotter to create a full visualization of an entire model.

plot_2D_fixed_phi
-----------------

In this model, a 2D slice going from [0,0,0] through some user-specified point is plotted as a line. This line indicates the shape of the detector response function along that path. Plotting 2D figures takes the same keywords as plotting 3D figures, with the ``dimensions`` keyword set to 2 and with the only additional keyword being ``position``. This keyword expects a 3-element list of X, Y, and Z coordinates indicating the point that the 2D slice should pass through. The limits for 2D plots are the same as for 3D plots, defined using the ``limts`` keyword and with the same default values. 2D plots always plot training points by default, but will only plot test points if a scorer is defined. Furthermore, 2D plots will only plot points that the 2D slice directly passes through. 

plot_2D_fixed_radius
--------------------

This model is identical to the "plot_2D_fixed_phi" model except that the point specifies a radial distance, not an angular slice. The plot generated for a fixed radius model will create a plot at all angles at a single radial distance from [0,0,0], with limits defined by the ``limits`` keyword (and with the same defaults as in the 3D plots).

plot_2D_fixed_line
------------------

This model defines the path between two points along a line. The only different keyword behavior here is that the ``position`` keyword expects a list of 3-element lists, in the form [ [X_1, Y_1, Z_1], [X_2, Y_2, Z_2] ]. The points provided must be within the limits of the plot.