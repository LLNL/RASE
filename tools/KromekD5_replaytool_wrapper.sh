#!/bin/bash
# Author: Samuele Sangiorgio <samuele@llnl.gov>
# This script wraps PCSOffline replay tool from Kromek so it processes entire folders

# Settings
RTEXE=/usr/bin/PCSOffline

# check input parameters are present and valid
if [ $# -lt 2 ]
then
    echo
    echo "Usage: $0 INPUTDIR OUTPUTDIR"
    echo
    exit $E_MISSING_POS_PARAM
fi

INPUTDIR=$1
OUTPUTDIR=$2

[ ! -d ${INPUTDIR} ] && echo "INPUTDIR not found" && exit 1
[ ! -d ${OUTPUTDIR} ] && echo "OUTPUTDIR not found" && exit 1

FILELIST="$INPUTDIR"/*

# loop over list of files in the input folder and run the RT
for FILE in $FILELIST
do
    # get the file basename
    BASENAME=${FILE##*/}
    BASENAME=${BASENAME%.*}
    
    # get the measurement time from within the file
    DWELLTIME=$(awk -F "\"*,\"*" 'NR==1 {print $3}' ${FILE}) 
    
    # run the replay tool
    $RTEXE $FILE $DWELLTIME ${OUTPUTDIR}/${BASENAME}.csv
    
done