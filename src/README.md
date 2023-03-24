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
The segmentation model must be trained first.  The input to the segmentation stage is also prepared in ``prepare_seg.sh``, so don't forget to make changes there if you want to change the input to the pipeline.
Takes a couple of minutes.
``sh run_pipeline.sh``

## Development Versions
These evaluate performance on the dev set, rather than the test set.  The only prerequisite is training the segmentation model.
``sh dev_seg.sh``
``sh dev_gloss.sh``
``sh dev_pipeline.sh``
