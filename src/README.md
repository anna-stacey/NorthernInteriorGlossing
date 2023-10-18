# Automatic Segmentation and Glossing

Put the data files (`train.txt`,  `dev.txt`, `test.txt`) into the `data` directory.  Your files should replace the small sample files that are included there.

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
There is a parameter in the shell scripts for specifying which line number contains the gloss - check that this is set correctly for the given language data!  
- To run on the dev set: ``sh src/dev_gloss.sh``
- To run on the test set: ``sh src/run_gloss.sh``

After running the above, run this to evaluate using the sigmorphon evaluation system (this code, eval.py, is not included in this repo):  
- ``python3 src/sigmorphon/eval.py --pred generated_data/gloss_pred.txt --gold generated_data/gloss_gold.txt``

## Run the Entire Pipeline
The segmentation model must be trained first, so make sure to run the correct one of ``dev_prepare_seg.sh`` or ``prepare_seg.sh`` first.  The input to the segmentation stage is also prepared in that step, so don't forget to make changes there if you want to change the input to the pipeline.  
Takes a couple of minutes.  
There is a parameter in the shell scripts for specifying which line number contains the gloss - check that this is set correctly for the given language data!  
- To run on the dev set: ``sh src/dev_pipeline.sh``
- To run on the test set: ``sh src/run_pipeline.sh``

After running the above, run this to evaluate using the sigmorphon evaluation system (this code, eval.py, is not included in this repo):  
- ``python3 src/sigmorphon/eval.py --pred generated_data/pipeline_pred.txt --gold generated_data/pipeline_gold.txt``
