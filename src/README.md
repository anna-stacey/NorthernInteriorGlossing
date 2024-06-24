# Automatic Segmentation and Glossing

Put your data files (`train.txt`,  `dev.txt`, `test.txt`) into the `data` directory.  Your files should replace the small sample files that are included there.

## Prescreen Your Data Files
To ensure compliance with the formatting anticipated by the segmenting and glossing systems.  Once you get 0 errors flagged here, you're ready to proceed.  
- `sh src/prescreen.sh`

## Preprocess and Train the Segmentation Model
- Takes a while. Gets all three datasets into the right format for fairseq, then trains fairseq (by calling train_seg.sh).  Once it's done running (i.e. when you see output telling you the last epoch has completed), you have to manually press enter to make it finish.
- To run on the dev set: ``sh src/dev_prepare_seg.sh``
- To run on the test set: ``sh src/prepare_seg.sh``

## Run the Segmentation Model
Takes a couple of mintutes.
- To run on the dev set: ``sh src/dev_seg.sh``
- To run on the test set: ``sh src/run_seg.sh``

## Run (and Train) the Glossing Model
Doesn't take any time.  
There is a parameter in the shell scripts for specifying which line number contains the gloss - check that this is set correctly for the given language data!  
- To run on the dev set: ``sh src/dev_gloss.sh``
- To run on the test set: ``sh src/run_gloss.sh``

After running the above, run this to evaluate using the sigmorphon evaluation system (this code, eval.py, is not included in this repo):  
- ``python3 src/sigmorphon/eval.py --pred generated_data/gloss_pred.txt --gold generated_data/gloss_gold.txt``

## Run the Entire Pipeline
The pipeline makes use of the segmentation predictions, so be sure to first [train](#preprocess-and-train-the-segmentation-model) and [run](#run-the-segmentation-model) the segmentation model.  
Takes a couple of minutes.  
There is a parameter in the shell scripts for specifying which line number contains the gloss - check that this is set correctly for the given language data!  
- To run on the dev set: ``sh src/dev_pipeline.sh``
- To run on the test set: ``sh src/run_pipeline.sh``

After running the above, run this to evaluate using the sigmorphon evaluation system (this code, eval.py, is not included in this repo):  
- ``python3 src/sigmorphon/eval.py --pred generated_data/pipeline_pred.txt --gold generated_data/pipeline_gold.txt``

## Extra Programs
You can compare two `..._pred.txt` output files with the simple ``compare_pred.py`` script:
``python3 src/compare_pred.py --file_1=generated_data/pipeline_pred.txt --file_2=generated_data/pipeline_pred_other.txt``
