.. _troubleshooting:

***************
Troubleshooting
***************

* While extensive testing has been performed, the current version of RASE is still being actively developed and therefore not expected to be free of bugs, especially related to the graphical interface and user experience. When unexpected behavior is observed, please notify the RASE development team at rase-support@llnl.gov.

* If RASE systematically crashes, either at start or during use, it is possible that the internal database might have become corrupt. The internal database is stored in a .sqlite file located in the RASE working directory. Removing that file will force RASE to create a new one from scratch. All the user information on scenarios and instruments will be unfortunately lost. The RASE development team may be able to recover data from a corrupt database if necessary.

* If a step after the “Run Replay Tool” step does not return the expected results, the most common culprit is that the replay tool was not correctly specified. In particular, confirm the Command Arguments field in the replay tool specification is correct for that tool.

* RASE creates various log files that can help identify the origin of a crash or unexpected behavior.

  * The main RASE log file ``rase.log`` resides in the same folder of the RASE executable and contains traceback information for unhandled exception causing the main code to crash
  * The output of the replay tool, if any, is saved in a file called ``replay_tool_output.log`` located in the sample directory for the specific scenario-instrument that is being replayed.
  * In case of errors when executing a results translator, a file called ``results_translator_output.log`` is created containing the output log of the translator tool. The file is located in the sample directory for the specific scenario-instrument that is being worked on.


A Note for Developers
=====================

* If any additional development is done to the source code by the user, it is recommended that the unit test suite is run periodically. Simply run the "test_main.py" file, which will automatically test various aspects of the main RASE functionality. In addition to the other requirements, the user must have "pytest" installed on their system to run this suite. 
