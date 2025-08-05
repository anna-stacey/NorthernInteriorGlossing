# NorthernInteriorGlossing
This repo provides a system that can be trained to automatically **gloss** language data.  Specifically, it takes in **unsegmented** language data, as input, and creates a **glossed** output (with a **segmented** version as an intermedite output). That is, the system learns to both **segment** (breaking down language data into its morphemes) and to **gloss** (providing a meaning for each of those morphemes).

This infrastucture was created as part of an [M.A. thesis](https://open.library.ubc.ca/soa/cIRcle/collections/ubctheses/24/items/1.0449331) at [UBC Linguistics](https://linguistics.ubc.ca), and funded in part by a CGS-M grant from [the Social Sciences and Humanities Research Council (SSHRC)](https://sshrc-crsh.canada.ca) of Canada.  Please see the main thesis document for a more detailed explanation of this project.

This system was developed to automate glossing for the three Northern Interior Salish languages -- nɬeʔkepmxcín, St'át'imcets, and Secwepemctsín.  The motivation is to accelerate the language documentation process, leading to more efficient production of glossed texts in these languages, useful to learners and linguists alike.  Because of the small amount of glossed data available for training, the project also employed strategies for cross-lingual learning (learning from related languages).

This document outlines key components of the infrastructure.  For running the code, check out the README in [src/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/src).

## Citation
Please cite this project as follows:
> Stacey, Anna. 2025. Automatic glossing for Northern Interior languages featuring cross-lingual enhancements. M.A. thesis, University of British Columbia. https://dx.doi.org/10.14288/1.0449331

## System Details
### Segmentation
The segmentation works by learning from pairs of unsegmented input data and segmented output data. For example, `train.input` contains a **list of words**, e.g. "t a o w e n m í n a s".  Then `train.output` contains the same list of words but with morpheme boundaries, e.g. "t a o w e n - m í n - a s".  So the model goes word-by-word and tries to learn where each word has morpheme boundaries.

The evaluation goes word by word and checks for an exact match. So the word is segmented correctly only if it has each morpheme boundary in the correct position and of the correct type (and hasn't messed up the characters in between).

### Glossing
The glossing model learns from sentences of **segmented** words in the language and the corresponding sentences of **glosses**. It breaks down each sentence into individual morphemes, using the given boundaries.  It **converts each morpheme into a set of features**: currently, this is just the whole morpheme itself, the last 3 characters of the morpheme, the previous morpheme in the sentence, and the following morpheme.  When training, it identifies each morpheme as a stem or gram (based on whether the corresponding gloss is in caps). Stems are just stored in a stem dictionary, and have their gloss replaced with `STEM`. So when the CRF is trained on pairs of features and their gloss, for stems it just learns that they *are* stems, whereas for bound morphemes it learns their gloss. On novel data, the CRF is used to gloss bound morphemes and identify stems, whose gloss is then looked up in the stem dictionary.  If that morpheme isn't in the stem dictionary, then the gloss predictions just gloss it as `STEM` (indicating an unknown stem).

### Pipeline
The pipeline code takes care of translating between the segmentation output and the glossing input.  So essentially it takes the lists of segmented words output by the segmentation model, and **reassembles** those into sentences.  And the glosses it just pulls from the original data like usual.  Then it proceeds with regular glossing!
- At present, the pipeline is doing a check to make sure that **infix boundaries are symmetrical**, i.e. a line contains the same number of "{" as "}" . The simplest approach for now is just to replace any rogue ones with a non-infixing boundary (e.g. `sqwa7>y-án-ak` -> `sqwa7-y-án-ak`), but this will not rememdy a case where the lone infix marker was in fact indicating an infix, and thus treating it as a regular morpheme will lead to a morpheme count mismatch.

## Data
You must provide glossed data in the language that you intend the model to learn to gloss.  Most of this data will be used for **training**, with some reserved for a separate round of improvements (**development**), and others still saved for evaluation, if so desired (**testing**).  Thus, the system expects to find a train, dev, and test file to work with.

For reference, tiny sample train/dev/test files are provided in `data/`, but should be replaced by your own three files.  The sample data is in St'át'imcets and comes from *Sqwéqwel’ Múta7 Sptakwlh: St’át’imcets Narratives* by Qwa7yán’ak (Alexander, 2016).

The expected data format is a list of sentences (with a newline in between each sentence).  However, there are no restrictions on the lengths of these sentences, so they could be a single word or actually contain mulitiple sentences written as one line.  Your glossed data must contain a minimum of three lines per sentence:
1. The **transcription** or **orthography** line
- This line is just a regular sentence in the target language, written normally.
- Example (from the sample `train.txt`):
    > Nilh ts7a ta skalúl7a wa7 tsicw káku7, taowenmínas áku7 i wa7 wa7 láku7 lta sk'emqína.
2. The **segmentation** line
- This line appears similar to (1), but it has punctuation added to mark morpheme boundaries.  Some of the morphemes themselves may be slightly different too, due to normalization processes.  Thus the segmentation line offers a morpheme-level breakdown of (1).
- Example:
    > nilh ts7a ta skalúl7-a wa7 tsicw káku7, taowen-mín-as áku7 i wa7 wá7 láku7 l-ta sk'em-qín-a.

3. The **gloss** line
- This line provides meaningful labels for every morpheme in (2).  Grammatical morphemes (*grams*) are given an abbreviated uppercase gloss, whereas lexical morphemes (*stems*) are given a full word in lowercase.
- Example:
    > COP this.VIS DET owl-EXIS IPFV get.there around+there town-RLT-TE to+there PL.DET IPFV be at.there.INVIS at-DET edge-top-EXIS

It's fine if the data contains more than three lines per sentence (e.g., a translation line), but these will be just be ignored by the system.  Ensure that you specify the correct line numbers for the lines of interest when you run the system.

There are strict expectations about the formatting of the glossed data, so that the code knows how to parse it.  These expectations, and other relevant info, are outlined in [data/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/data).  There is also a script for screening your data to check if these expectations are met, and some other tools that may be useful for working with your data.  These are found in (and described in) [src/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/src).

## Evaluation
### Segmentation
##### Word-level accuracy:
For each word, checks whether the segmented output *exactly matches* the gold output word.  This means inserting boundaries of the correct type in the correct location, and not inserting any incorrect boundaries.  
> Example:  
gold: *morpheme1-morpheme2*  
predicted: *morpheme1-morpheme2*  
score: 1/1 word correct   
predicted: *morpheme1=morpheme2*  
score: 0/1 word correct  
predicted: *morpheme1-morph-eme2*  
score: 0/1 word correct

It also goes beyond just boundaries to the morphemes themselves: performing any necessary normalization changes, while otherwise maintaining the input form.
> Example:
gold: *qeʔním[-t]-∅-ne*  
predicted: *qeʔním[-t]-∅-ne*  
score: 1/1 word corrrect  
predicted: *qeʔním-ne*  
score: 0/1 word corrrect  
predicted: *qeʔním[-t]-∅-ene*  
score: 0/1 word corrrect  

##### Out-of-Vocabulary (OOV) Accuracy
We also report a subset of the word-level accuracy, which considers only those words that are OOV (i.e., not seen in training).  This gives a sense of how well the model is applying patterns it learns to 'new' words.

##### Boundary-Level Precision, Recall and F1 (ROUGH DRAFT - CODE BEING EDITED)
This metric is focussed on the insertion of boundaries.  Although it is inevitably affected by normalization/other changes to the text when they affect the index of the boundaries within the word, such changes are not as central to this metric as they are to the word-level accuracy.  
Here, we look at each boundary that the system is meant to insert into the transcribed words.  Each boundary has an intended position in the word (counting from the leftmost edge of the word, e.g., there are boundaries at positions, 7, 10, and 12 in *qeʔním[-t]-∅-ne*, with the first position being 0), as well as an intended type (the boundary symbol used, e.g, all hyphens in *qeʔním[-t]-∅-ne*).  So for each gold boundary, we ask: did the model successfully put in a boundary of this type at this position?  To explicitly outline how this is determined:
- Go through every predicted boundary, and determine:
    - Is there a gold boundary at this position and of this type?
        - If yes, that's a **true positive**, because the model inserted a correct boundary!
        - If no, that's a **false positive**, because the model inserted an incorrect boundary.
- For every position where there isn't a predicted boundary, check if there is one in the gold.
    - If yes, that's a **false negative**, because the model failed to insert a correct boundary!
    - If not, that's a **true negative**, because the model successfully did not insert a boundary where there isn't meant to be one.  We don't need to count these, because they are not used in our calculations.
> Example:  
gold: *s-qyéytn*  
predicted: *s-qyéytn*  
true positives: 1  
false positives: 0  
false negatives: 0  
precision: 100%  
recall: 100%  
F1: 100%  
predicted: *sqyéytn*  
true positives: 0  
false positives: 0  
false negatives: 1  
precision: N/A  
recall: 0%  
F1: N/A  
predicted: *s-qyéy-tn*  
true positives: 1  
false positives: 1  
false negatives: 0  
precision: 50%  
recall: 100%  
F1: 67%

Furthermore, what about the case where we predict a boundary, and there is a boundary there in the gold output, but it's of a different type?
- That's both a **false positive** (because an incorrect boundary was inserted) and a **false negative** (because a correct boundary was not outputted).
> Example:
gold: *s-qyéytn*  
predicted: *s=qyéytn*  
true positives: 0  
false positives: 1  
false negatives: 1  
precision: 0%  
recall: 0%  
F1: 0%  

This is a bit odd, because it means that, as illustrated by the examples of predicting *sqyéytn* vs. *s=qyéytn*, predicting a boundary in the right place but of the wrong type results in a worse score than just failing to predict the boundary altogether.  **Option: run a version of these metrics that is indifferent to boundary type, as well.**

Like other word-level evaluations, this metric is susceptible to ECF since we evaluate from left-to-right in the word.  Thus, mistakes earlier in the word result in lower scores than equivalent mistakes later in the word.
> Example:  
gold: *kʷukʷ-s-cút-s*  
predicted: *kʷukʷs-cút-s*  
true positives: 0  
false positives: 2  
false negatives: 3  
precision:  0%
recall: 0%  
F1: 0%  
> Example:  
predicted: *kʷukʷ-s-cúts*  
true positives: 2  
false positives: 0  
false negatives: 1  
precision: 100%  
recall: 67%  
F1: 80%  

Finally, as mentioned, these counts can also be affected by normalization or other changes to the wordform itself.  For example, if the model either misses a correct normalization or performs an unnecessary normalization (in a way that affects the *number* of characters), this will throw off the position of boundaries in the rest of the word.
> Example:  
input: *kʷukʷscúc*  
gold output: *kʷukʷ-s-cút-s*  
predicted output: *kʷukʷ-s-cú-s*  
true positives: 2  
false positives: 1  
false negatives: 1  
precision: 67%  
recall: 67%  
F1: 67%  

We use the **precision** metric to evaluate what portion of the predicted boundaries were correct (ignoring for now additional correct boundaries that the model failed to predict):
> precision = true positives / (true positives + false positives)

We use the **recall** metric to evaluate how many of the correct boundaries the system managed to predict (ignoring for now additional incorrect boundary predictions made by the model):
> recall = true positives / (true positives + false negatives)

In order to consider all of these factors (i.e., getting all the right boundaries without predicting lots of wrong boundaries), we combine the precision and recall into the **F1 score**, the harmonic mean of precision and recall:
> F1 = (2 * precision * recall) / (precision + recall)

### Glossing
##### Morpheme-level accuracy:  
Breaks down each sentence into words.  Within each word, it goes through the gold morphemes left-to-right and checks whether the predicted output has the correct morpheme in the same order.  
> Example:  
gold: *morpheme1-morpheme2*  
predicted: *morpheme2-morpheme1*  
score: 0/2 morphemes correct  

This process is straightforward for the glossing output, where there is always the same number of morphemes in the gold and predicted words, but has some quirks for the pipeline output, where that correspondence is not guaranteed.  In particular, if a sentence has some morphemes correct but the correspondence between gold and predicted morphemes is off due to the wrong number of predicted morphemes, the score will be greatly reduced.  
> Example:  
gold: *morpheme1-morpheme2-morpheme3*  
predicted: *morpheme2-morpheme3*  
score: 0/3 morphemes correct  

Also, if there are extra predicted morphemes at the end of a word, these will not affect its score as we are only checking gold morphemes.  
> Example:  
gold: *morpheme1-morpheme2*  
predicted: *morpheme1-morpheme2-morpheme3*  
score: 2/2 morphemes correct

##### Word-level accuracy:
This check work similarly to the morpheme-level accuracy, but it marks each word as correct if *all* the morphemes within it are correct, and as incorrect otherwise.  
> Example:  
gold: *morpheme1-morpheme2*  
predicted: *morpheme1-morpheme3*  
score: 0/1 words correct (because it has only 1/2 morphemes correct)

Like the previous check, it checks all gold morphemes, meaning a word can still be marked as correct if it has erroneous morphemes added to its end.
> Example:  
gold: *morpheme1-morpheme2*  
predicted: *morpheme1-morpheme2-morpheme3*  
score: 1/1 words correct

##### Stem and gram accuracy
These checks are morpheme-level accuracy checks that separate out the results for stems and for grams.
The 'predicted' version of these checks is concerned with the morphemes that the system *predicts* are stems or grams, regardless of their actual status (in the gold).  So if a morpheme is stem, but the system erroneously categorizes it as a gram, its result is being included in the **gram accuracy**.  
> Example:  
gold: *GRAM1-stem1*  
predicted: *GRAM1-GRAM2*  
stem score: N/A (no stems)  
gram score: 1/2 gram morphemes correct  

This also means that, unlike the general morpheme-level accuracy check, it is checking the accuracy of every *predicted* morpheme, regardless of whether it has a gold counterpart.  And it will ignore gold morphemes that do not have a predicted counterpart.
> Example:  
gold: *GRAM1-stem1*  
predicted: *GRAM1-GRAM2-GRAM3*  
stem score: N/A (no stems)
gram score: 1/3 gram morphemes correct  

> Example:  
gold: *GRAM1-stem1-GRAM3*  
predicted: *GRAM1-GRAM2*  
stem score: N/A (no stems)
gram score: 1/2 gram morphemes correct  

And of course, these checks are still at the mercy of broken correspondences between morphemes in the gold and predicted words.
> Example:  
gold: *GRAM1-stem1*  
predicted: *GRAM1-GRAM2-stem1*  
stem score: 0/1 stem morphemes correct
gram score: 1/2 gram morphemes correct  

### Pipeline
At the pipeline stage, we repeat the glossing stage checks, with some caveats.  Since the alignment between morphemes is no longer guaranteed, the morpheme-level score (and by extension, the word-level score, since it is just a summary of the morpheme-level score for all the morphemes in a given word) can suffer from ECF as it goes from left-to-right through a word's morphemes.  
We also use the word-level accuracy metric from the segmentation stage, which differs from the glossing word-level score in that it takes boundary *type* into consideration.
> Example:  
gold: morpheme1-morpheme2  
predicted: morpheme1~morpheme2
glossing word-level accuracy: 1/1 words
segmentation word-level accuracy: 0/1 words

Thus, we can compare these two scores to see how many words were incorrect only in boundary type.

Overall, the segmentation stage word-level accuracy is the more sensible metric here, simply asking: did we correctly segment (insert boundaries of the right type in the right spots, performing normalization where needed but otherwise maintaining the input form) *and* gloss (provide the correct label for every morpheme) the entire word?

##### Bag o' Words
As mentioned, the glossing stage morpheme-level score doesn't work so well at the pipeline stage, because of the impact of ECF from earlier in the word.  But a morpheme-level evaluation is nice for providing a more fine-grained view than a word-level one.  We therefore use this metric as a kind of morpheme-level accuracy more suited to the pipeline: we don't care about the order/alignment of the glosses, just that they're present.  This score is basically a more forgiving version of the other morpheme-level accuracy, so it must be greater than or equal to that score.  
For each word, we go through its gold glosses one-by-one.  We check if each is present *somewhere* in the set of predicted glosses for this word.  Notably, if it is, we *remove* it, so that each predicted morpheme can only be counted once.  This probably isn't super impactful, as its unlikely the same gloss appears multiple times in one word.  
This score is reported at the morpheme level.  So the bag o' words score is the number of gold morphemes that were correctly predicted *somewhere* in the word (excluding duplicates), divided by the total number of gold morphemes.  

> Example:  
gold: *morpheme1-morpheme2*  
predicted: *morpheme2-morpheme1*  
score: 2/2 morphemes correct  

> Example:  
gold: *morpheme1-morpheme2-morpheme3*  
predicted: *morpheme2-morpheme3*  
score: 2/3 morphemes correct  

> Example:  
gold: *morpheme1-morpheme-1-morpheme2*  
predicted: *morpheme2-morpheme1-morpheme3*  
score: 2/3 morphemes correct  

## References
Alexander, Carl. 2016. *Sqwéqwel’ múta7 sptakwlh: St̓át̓imcets Narratives by Qwa7yán’ak (Carl Alexander)*. Recorded, transcribed, translated and edited by Elliott Callahan, Henry Davis, John Lyon & Lisa Matthewson. Vancouver and Lillooet, Canada: University of British Columbia Occasional Papers in Linguistics and the Upper St’át’imc Language, Culture and Education Society (USLCES).
