# Automatic Segmentation and Glossing

## Create the Train, Dev, and Test Datasets
- For St̓át̓imcets: ``python3 src/split_statimcets_data.py``
- For Gitksan (data *not* in repo):``python3 src/split_gitksan_data.py``

## Preprocess and Train the Segmentation Model
- Takes a while. Gets all three datasets into the right format for fairseq, then trains fairseq (by calling train_seg.sh).
- To run on the dev set: ``sh src/dev_prepare_seg.sh``
- To run on the test set: ``sh src/prepare_seg.sh``

## Run the Segmentation Model
Takes a couple of mintutes.
- To run on the dev set: ``sh src/dev_seg.sh``
- To run on the test set: ``sh src/run_seg.sh``

## Run (and Train) the Glossing Model
Doesn't take any time.
- To run on the dev set: ``sh src/dev_gloss.sh``
- To run on the test set: ``sh src/run_gloss.sh``

## Run the Entire Pipeline
The segmentation model must be trained first, so make sure to run the correct one of ``dev_prepare_seg.sh`` or ``prepare_seg.sh`` first.  The input to the segmentation stage is also prepared in that step, so don't forget to make changes there if you want to change the input to the pipeline.
Takes a couple of minutes.
- To run on the dev set: ``sh src/dev_pipeline.sh``
- To run on the test set: ``sh src/run_pipeline.sh``
