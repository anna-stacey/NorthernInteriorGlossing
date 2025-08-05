# NorthernInteriorGlossing
This repo provides all the necessary tools for creating a system to automatically **gloss** language data.  Specifically, the system takes in **unsegmented** language data, as input, and creates a **glossed** output (with a **segmented** version as an intermedite output). That is, the system learns to both **segment** (breaking down language data into its morphemes) and to **gloss** (providing a meaning for each of those morphemes).

This infrastucture was created as part of an [M.A. thesis](https://open.library.ubc.ca/soa/cIRcle/collections/ubctheses/24/items/1.0449331) at [UBC Linguistics](https://linguistics.ubc.ca) supervised by [Miikka Silfverberg](https://mpsilfve.github.io), and funded in part by a CGS-M grant from [the Social Sciences and Humanities Research Council (SSHRC)](https://sshrc-crsh.canada.ca) of Canada.  Please see the main thesis document for a more detailed explanation of this project.

This system was developed to automate glossing for the three Northern Interior Salish languages -- nɬeʔkepmxcín, St'át'imcets, and Secwepemctsín.  The motivation is to accelerate the language documentation process, leading to more efficient production of glossed texts in these languages, useful to learners and linguists alike.  Because of the small amount of glossed data available for training, the project also employed strategies for cross-lingual learning (learning from related languages).

This document outlines key components of the infrastructure.  For running the code, check out the README in [src/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/src).

## Citation
Please cite this project as follows:
> Stacey, Anna. 2025. Automatic glossing for Northern Interior languages featuring cross-lingual enhancements. M.A. thesis, University of British Columbia. https://dx.doi.org/10.14288/1.0449331

## System Details
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

The expected data format is a list of sentences (with a newline in between each sentence).  However, there are no restrictions on the lengths of these sentences, so they could be a single word or actually contain mulitiple sentences written as one line.  Your glossed data must contain a minimum of three lines per sentence:
1. The **transcription** or **orthography** line
- This line is just a regular sentence in the target language, written normally.
- Example (from the sample `train.txt`):
    > Nilh ts7a ta skalúl7a wa7 tsicw káku7, taowenmínas áku7 i wa7 wa7 láku7 lta sk'emqína.
2. The **segmentation** line
- This line appears similar to (1), but it has symbols added to mark morpheme boundaries.  Some of the morphemes themselves may be slightly different too, due to normalization processes.  Thus the segmentation line offers a morpheme-level breakdown of (1).
- Example:
    > nilh ts7a ta skalúl7-a wa7 tsicw káku7, taowen-mín-as áku7 i wa7 wá7 láku7 l-ta sk'em-qín-a.

3. The **gloss** line
- This line provides meaningful labels for every morpheme in (2).  Grammatical morphemes (*grams*) are given an abbreviated uppercase gloss, whereas lexical morphemes (*stems*) are given a full word in lowercase.
- Example:
    > COP this.VIS DET owl-EXIS IPFV get.there around+there town-RLT-TE to+there PL.DET IPFV be at.there.INVIS at-DET edge-top-EXIS

It's fine if the data contains more than three lines per sentence (e.g., a translation line), but these will be just be ignored by the system.  Ensure that you specify the correct line numbers for the lines of interest when you run the system.

There are strict expectations about the formatting of the glossed data, so that the code knows how to parse it.  These expectations, and other relevant info, are outlined in [data/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/data).  There is also a script for screening your data to check if these expectations are met, and some other tools that may be useful for working with your data.  These are found in (and described in) [src/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/src).

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

## References
Alexander, Carl. 2016. *Sqwéqwel’ múta7 sptakwlh: St̓át̓imcets Narratives by Qwa7yán’ak (Carl Alexander)*. Recorded, transcribed, translated and edited by Elliott Callahan, Henry Davis, John Lyon & Lisa Matthewson. Vancouver and Lillooet, Canada: University of British Columbia Occasional Papers in Linguistics and the Upper St’át’imc Language, Culture and Education Society (USLCES).

Lafferty, John, Andrew McCallum & Fernando Pereira. 2001. Conditional Random Fields:
Probabilistic Models for Segmenting and Labeling Sequence Data. *Proceedings of the
Eighteenth International Conference on Machine Learning*, 282–289. San Francisco,
California: Morgan Kaufmann Publishers Inc.

Ott, Myle, Sergey Edunov, Alexei Baevski, Angela Fan, Sam Gross, Nathan Ng, David Grangier & Michael Auli. 2019. fairseq: A Fast, Extensible Toolkit for Sequence Modeling. In Waleed Ammar, Annie Louis & Nasrin Mostafazadeh (eds.), *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics (Demonstrations)*, 48–53. Minneapolis, Minnesota: Association for Computational Linguistics.

Vaswani, Ashish, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser & Illia Polosukhin. 2017. Attention Is All You Need. *Advances in Neural Information Processing Systems*(30), 5998–6008.
