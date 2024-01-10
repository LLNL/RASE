#!/bin/bash
# Author: Steven Czyz <czyz1@llnl.gov>
#         Modified from wrapper written by Samuele Sangiorgio <samuele@llnl.gov>
# This script wraps WebID replay tool so it processes entire folders

# Settings
# check input parameters are present and valid
if [ $# -lt 4 ]
then
    echo
    echo "Usage: $0 RTEXE INPUTDIR OUTPUTDIR DRF"
    echo
    exit $E_MISSING_POS_PARAM
fi

RTEXE=$1
INPUTDIR=$2
OUTPUTDIR=$3
DRF=$4

[ ! -d ${INPUTDIR} ] && echo "INPUTDIR not found" && exit 1
if [ ! -d ${OUTPUTDIR} ]
then
    mkdir ${OUTPUTDIR}
fi
[ ! -d ${OUTPUTDIR} ] && echo "OUTPUTDIR not found" && exit 1

FILELIST="$INPUTDIR"/*.n42

RTFOLDER="$(dirname "${RTEXE}")"
RTFILE="$(basename "${RTEXE}")"

cd "$RTFOLDER"
# loop over list of files in the input folder and run the RT
for FILE in $FILELIST
do
    # get the file basename
    BASENAME=${FILE##*/}
    BASENAME=${BASENAME%.*}
    # run webid
    ./$RTFILE --mode=command-line --drf=$DRF $FILE --out-format=json > ${OUTPUTDIR}/${BASENAME}.json

done
cd -