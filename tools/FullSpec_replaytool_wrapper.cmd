:: This Windows batch script wraps WebID so it processes entire folders

@echo off
setlocal EnableDelayedExpansion

set "executable_path=%1"
set "input_folder=%2"
set "output_folder=%3"
set "drf=%4"

if not defined executable_path (
  echo Error: Executable path not specified.
  echo Usage: %0 [executable_path] [input_folder] [output_folder] [drf]
  exit /b 1
)

if not exist "%executable_path%" (
  echo Error: Executable does not exist: %executable_path%
  exit /b 1
)

if not defined input_folder (
  echo Error: Input folder not specified.
  echo Usage: %0 [executable_path] [input_folder] [output_folder] [drf]
  exit /b 1
)

if not exist "%input_folder%" (
  echo Error: Input folder does not exist: %input_folder%
  exit /b 1
)

if not defined output_folder (
  echo Error: Output folder not specified.
  echo Usage: %0 [executable_path] [input_folder] [output_folder] [drf]
  exit /b 1
)

if not exist "%output_folder%" (
  echo Creating output folder: %output_folder%
  mkdir "%output_folder%"
)

if not defined drf (
  echo Error: drf parameter not specified.
  echo Usage: %0 [executable_path] [input_folder] [output_folder] [drf]
  exit /b 1
)


for %%f in ("%input_folder%\*") do (
  echo Processing file: %%f
  set "output_file=%output_folder%\%%~nf.json"
  "%executable_path%" --out-format=json --mode=command-line --drf="%drf%" "%%f" > "!output_file!"
)

echo All files processed.
