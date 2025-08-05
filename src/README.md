# Running the Scripts
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

> Note: At present, the pipeline is doing a check to make sure that **infix boundaries are symmetrical**, i.e., each line contains the same number of "{" as "}" . The simplest approach for abiding by this is just to replace any rogue ones with a non-infixing boundary (e.g. `sqwa7>y-án-ak` -> `sqwa7-y-án-ak`), but this will not remedy a case where the lone infix marker was in fact indicating an infix, and thus treating it as a regular morpheme will lead to a morpheme count mismatch.

## Extra Programs
You can compare two `..._pred.txt` output files with the simple ``compare_pred.py`` script:
``python3 src/compare_pred.py --check_gloss_line --file_1=generated_data/pipeline_pred.txt --file_2=generated_data/pipeline_gold.txt``

## Multiple Rounds of Training (with Different Training Sets)
This process was used for the monolingual fine-tuning discussed in the thesis, where we do a round of training on the multilingual data, followed by a round of training on the monolingual data only.  For simplicity, I refer to these two rounds as 'pre-training' and 'training' in the steps below:
- Create a .txt that contains ALL the data, i.e., the data for pre-training combined with the data for training.
- Run `fairseq-preprocess` (as in `prepare_seg.sh`) on the total dataset, so that a `dict.input.txt` and `dict.output.txt` are generated.  Move this to a directory where they won't get overwritten (for this example, I put them in a folder called `total-train/`)
- Now you are ready to pre-train.  Note that you may want to also use a suitable dev file.  When you run `fairseq-preprocess` this time, tell it to use the big dict files by adding `--srcdict total-train/dict.input.txt --tgtdict total-train/dict.output.txt` to the command.
- With pre-training complete, make sure you leave the models that were created as is.
- For the regular training, change max-epoch in `train_seg.sh` to be the number of pre-training epochs + the number of regular training epochs (because the regular training is seen as a continuation of the previous epochs, not a restart).
- Now run regular training in the exact same way as the pre-training, including with the extra command line args.
- By the way, specifically for the monolingual fine-tuning case, when you're running `dev_seg.sh` to predict and evaluate, you should first re-generate `train.output`.  Otherwise, you'll end up with OOV proportions/scores based only on the monolingual training set.  You can do so by re-running `dev_prepare_seg.sh`, and changing the train set back to the combined one, and commenting out the call to  `train_seg.sh`.  Or you could just store the file initially!