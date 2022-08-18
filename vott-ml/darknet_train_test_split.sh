#!/bin/bash
# Check for valid path to vott output
echo "ARG: $1";
DIR_EXISTS=$(ls | grep "$1" | wc -l)
if [[ $DIR_EXISTS == 0 ]]; then
  echo "Error, Directory to VOTT output not passed as argument to this script. Exiting.";
  exit
fi
echo "Found directory $1. Attempting parsing..."
# Move the classes file out
CLASSES_EXIST=$(ls $1 | grep "classes.txt" | wc -l)
if [[ $CLASSES_EXIST == 0 ]]; then
  echo "Error, Directory does not contain classes.txt file. Exiting.";
  exit
fi
mv "$1/classes.txt" classes.txt
# Get number of entries
DIR_ENTRY_COUNT=$(ls $1 | grep .txt | wc -l)
echo $DIR_ENTRY_COUNT
# Make output directories, files
touch valid.txt train.txt
mkdir labels
mkdir labels/train
mkdir labels/test
# Loop over all train data and make a train/test split
for ENTRY in $(ls $1 | grep .txt)
do
  # 80/20 split on data
  PARSE=$(( $RANDOM % 5 ))
  if [[ $PARSE == 1 ]]
  then
    cp $1/$ENTRY labels/test/$ENTRY
    IMAGE=$(echo $ENTRY | cut -d '.' -f 1).jpg
    # cp $1/$IMAGE test/$IMAGE
    echo "$(pwd)/$1/$IMAGE" >> valid.txt
  else
    cp $1/$ENTRY labels/train/$ENTRY
    IMAGE=$(echo $ENTRY | cut -d '.' -f 1).jpg
    # cp $1/$IMAGE train/$IMAGE
    echo "$(pwd)/$1/$IMAGE"  >> train.txt
  fi
done
# Clean up
cp classes.txt "$1/classes.txt"
