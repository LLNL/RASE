:: This Windows script is a wrapper for the FLIR-R440 / TARGET F-500 Replay Tool
:: Place this script in the same folder as Target.NID.ReplayTool.exe
:: 2018-10-26 Samuele Sangiorgio <sangiorgio1@llnl.gov>

@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

:: execute from the parent folder
cd /d %~dp0

:: Check command line input. Expect input and output folders
SET missing_param=0
IF [%1]==[] SET missing_param=1
IF [%2]==[] SET missing_param=1
IF /I %missing_param% EQU 1 (
  ECHO Usage: %~n0 input_folder output_folder
  EXIT /B 1
)

Target.NID.ReplayTool.exe %1

:: Moving results to output folder
:: Note that this fails if %2 already exists as a file
IF NOT EXIST %2\ (mkdir %2)
move /Y %1\*.res %2 >nul
move /Y %1\summary.txt %2 >nul
