# Automatic Segmentation and Glossing for Gitksan

## Create the Train, Dev, and Test Datasets
``python3 split_dataset.py``

## Preprocess and Train the Segmentation Model
Takes a while.
``sh prepare_seg.sh``

## Run the Segmentation Model
Takes a couple of mintutes.
``sh run_seg.sh``

## Run (and Train) the Glossing Model
Doesn't take any time.
``sh run_gloss.sh``

## Run the Entire Pipeline
The segmentation model must be trained first. 
Takes a couple of minutes.
``sh run_pipeline.sh``
