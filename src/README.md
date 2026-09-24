
# Scripts
## Contents
- [Automatic Glossing System Details](#automatic-glossing-system-details)
- [Running the Scripts](#running-the-scripts)
- [References](#references)

## Automatic Glossing System Details
### Segmentation
The segmentation works by learning from pairs of unsegmented input data and segmented output data. For example, `train.input` contains a **list of words**, e.g. the word "t a o w e n m í n a s" (with spaces inserted between characters).  Then, `train.output` contains the same list of words but with morpheme boundaries added , e.g. "t a o w e n - m í n - a s".  So the model goes word-by-word and tries to learn where each word has morpheme boundaries.

The segmenting stage uses a transfomer model (Vaswani et al., 2017) via [fairseq](https://github.com/facebookresearch/fairseq) (Ott et al., 2019).

The evaluation goes word-by-word and checks for an exact match. So the word is segmented correctly only if it has each morpheme boundary in the correct position and of the correct type (and hasn't messed up the characters in between).  This is the **word-level segmentation accuracy**.  Other metrics used are provded in [the below section](#evaluation) covering evaluation.

### Glossing
The glossing model learns from sentences of **segmented** words in the language and the corresponding sentences of **glosses**. It breaks down each sentence into individual morphemes, using the given boundaries.  It **converts each morpheme into a set of hand-selected features**: the whole morpheme itself, the last 3 characters of the morpheme, the previous morpheme in the sentence, the following morpheme etc.  To prepare for training, stem morphemes get stored in a simple stem dictionary, and have their gloss replaced with `STEM`. Next, a model is trained on pairs of features and their gloss.  Because of the `STEM` replacement, the model just learns to *identify* stems as stems, whereas for grams, it actually learns their gloss label.

When using the model to gloss new data, the model is first used to gloss grams and identify stems.  Next, morphemes identified as stems have their gloss looked up in the stem dictionary.  If that morpheme isn't in the stem dictionary, then it simply keeps the gloss `STEM` (indicating an unknown stem).

Conditional random fields (CRFs) (Lafferty et al., 2001) are used for the glossing-stage model, via [sklearn-crfsuite](https://github.com/TeamHG-Memex/sklearn-crfsuite).

### Pipeline
The pipeline code takes care of translating between the segmentation output and the glossing input.  That is, it runs both the segmenting and glossing sub-stages in order, and ensures that the segmentation output gets correctly fed as input to the glossing system.

Essentially, it takes the lists of segmented words output by the segmentation model, and **reassembles** those into sentences.  And the glosses it just pulls from the original data like usual.  Then it proceeds with regular glossing!

## Data
You must provide glossed data in the language that you intend the model to learn to gloss.  Most of this data will be used for **training**, with some reserved for a separate round of improvements (**development**), and others still saved for evaluation, if so desired (**testing**).  Thus, the system expects to find a train, dev, and test file to work with.

For reference, tiny sample train/dev/test files are provided in `data/`, but should be replaced by your own three files.  The sample data is in St'át'imcets and comes from *Sqwéqwel’ múta7 sptakwlh: St̓át̓imcets Narratives by Qwa7yán’ak (Carl Alexander)*  (Alexander, 2016).

There are strict expectations about the formatting of the glossed data, so that the code knows how to parse it.  These expectations, and other relevant info, are outlined in [data/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/data).  

## Evaluation
As part of this project, careful consideration was put into what metrics to use to evaluate the system's performance.  Several metrics were selected for segmenting, glossing, and their combination (the pipeline), which taken altogether help provide a sense of how well the system is working, and where its strengths and shortcomings lie.

A list of the metrics used at each stage is given below.  Please check out `4.4 Evaluation` in the thesis documentation for extensive discussion of each metric: motivations, what it tells us (and what it doesn't), example evaluations, how it's calculated.
- Segmentation stage:
    - Word-level accuracy
        - Across all words
        - On OOV (out-of-vocabulary; i.e., unseen during training) words only
    - Boundary-level precision, recall, and F1
        - Type-sensitive (where a boundary in the right place of the wrong type is wrong)
        - Type-insensitive (where a boundary in the right place of the wrong type is right)
    - Boundary count ratio
- Glossing stage:
    - Word-level accuracy
    - Morpheme-level accuracy
        - Across all morphemes
        - On stems only
        - On IV (in-vocabulary; i.e., seen during training) stems only
        - On grams only
- Pipeline:
    - Word-level accuracy
        - Across all words
        - On OOV (out-of-vocabulary; i.e., unseen during training) words only
    - Morpheme-level accuracy
        - Default appraoch (left-to-right, in order)
        - Bag-of-words approach

## Running the Scripts
Put your data files (`train.txt`,  `dev.txt`, `test.txt`) into the `data` directory.  Your files should replace the small sample files that are included there.

### Prescreen Your Data Files
To ensure compliance with the formatting anticipated by the segmenting and glossing systems.  Once you get 0 errors flagged here, you're ready to proceed.  
- `sh src/prescreen.sh`

### Preprocess and Train the Segmentation Model
- Takes a while. Gets all three datasets into the right format for fairseq, then trains fairseq (by calling `train_seg.sh`).  Note that once it's done running (i.e., when you see output telling you the last epoch has completed), you have to manually press enter to make it finish.
- To run on the test set: ``sh src/prepare_seg.sh``

### Run the Segmentation Model
Takes a couple of mintutes.
- To run on the test set: ``sh src/run_seg.sh``

### Run (and Train) the Glossing Model
Doesn't take any time.  
There is a parameter in the shell scripts for specifying which line number contains the gloss - check that this is set correctly for the given language data!  
- To run on the test set: ``sh src/run_gloss.sh``

After running the above, run this to evaluate using the sigmorphon evaluation system (this code, eval.py, is not included in this repo):  
- ``python3 src/sigmorphon/eval.py --pred generated_data/gloss_pred.txt --gold generated_data/gloss_gold.txt``

### Run the Entire Pipeline
The pipeline makes use of the segmentation predictions, so be sure to first [train](#preprocess-and-train-the-segmentation-model) and [run](#run-the-segmentation-model) the segmentation model.  
Takes a couple of minutes.  
There is a parameter in the shell scripts for specifying which line number contains the gloss - check that this is set correctly for the given language data!  
- To run on the test set: ``sh src/run_pipeline.sh``

After running the above, run this to evaluate using the sigmorphon evaluation system (this code, eval.py, is not included in this repo):  
- ``python3 src/sigmorphon/eval.py --pred generated_data/pipeline_pred.txt --gold generated_data/pipeline_gold.txt``

> Note: At present, the pipeline is doing a check to make sure that **infix boundaries are symmetrical**, i.e., each line contains the same number of "{" as "}" . The simplest approach for abiding by this is just to replace any rogue ones with a non-infixing boundary (e.g. `sqwa7>y-án-ak` -> `sqwa7-y-án-ak`), but this will not remedy a case where the lone infix marker was in fact indicating an infix, and thus treating it as a regular morpheme will lead to a morpheme count mismatch.

### Extra Programs
You can compare two `..._pred.txt` output files with the simple ``compare_pred.py`` script:
``python3 src/compare_pred.py --check_gloss_line --file_1=generated_data/pipeline_pred.txt --file_2=generated_data/pipeline_gold.txt``

### Multiple Rounds of Training (with Different Training Sets)
This process was used for the monolingual fine-tuning discussed in the thesis, where we do a round of training on the multilingual data, followed by a round of training on the monolingual data only.  For simplicity, I refer to these two rounds as 'pre-training' and 'training' in the steps below:
- Create a .txt that contains ALL the data, i.e., the data for pre-training combined with the data for training.
- Run `fairseq-preprocess` (as in `prepare_seg.sh`) on the total dataset, so that a `dict.input.txt` and `dict.output.txt` are generated.  Move this to a directory where they won't get overwritten (for this example, I put them in a folder called `total-train/`)
- Now you are ready to pre-train.  Note that you may want to also use a suitable dev file.  When you run `fairseq-preprocess` this time, tell it to use the big dict files by adding `--srcdict total-train/dict.input.txt --tgtdict total-train/dict.output.txt` to the command.
- With pre-training complete, make sure you leave the models that were created as is.
- For the regular training, change max-epoch in `train_seg.sh` to be the number of pre-training epochs + the number of regular training epochs (because the regular training is seen as a continuation of the previous epochs, not a restart).
- Now run regular training in the exact same way as the pre-training, including with the extra command line args.
- By the way, specifically for the monolingual fine-tuning case, when you're running `run_seg.sh` to predict and evaluate, you should first re-generate `train.output`.  Otherwise, you'll end up with OOV proportions/scores based only on the monolingual training set.  You can do so by re-running `prepare_seg.sh`, and changing the train set back to the combined one, and commenting out the call to  `train_seg.sh`.  Or you could just store the file initially!

## References
Lafferty, John, Andrew McCallum & Fernando Pereira. 2001. Conditional Random Fields:
Probabilistic Models for Segmenting and Labeling Sequence Data. *Proceedings of the
Eighteenth International Conference on Machine Learning*, 282–289. San Francisco,
California: Morgan Kaufmann Publishers Inc.

Ott, Myle, Sergey Edunov, Alexei Baevski, Angela Fan, Sam Gross, Nathan Ng, David Grangier & Michael Auli. 2019. fairseq: A Fast, Extensible Toolkit for Sequence Modeling. In Waleed Ammar, Annie Louis & Nasrin Mostafazadeh (eds.), *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics (Demonstrations)*, 48–53. Minneapolis, Minnesota: Association for Computational Linguistics.

Vaswani, Ashish, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser & Illia Polosukhin. 2017. Attention Is All You Need. *Advances in Neural Information Processing Systems*(30), 5998–6008.
