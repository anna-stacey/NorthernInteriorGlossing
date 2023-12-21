# Automatic Glossing
## Data
For reference, tiny sample train/dev/test files are provided in `data/`, but should be replaced by your own three files.  The sample data comes from *Sqwéqwel’ Múta7 Sptakwlh: St’át’imcets Narratives* by Qwa7yán’ak (Alexander, 2016).

## Data Expectations
The system uses the transcription, segmentation and glossing line.  The translation line is not presently used, but it is fine if the data includes this (or other extraneous lines).  The script files may need to be edited to indicate which line number contains the segmentation, gloss etc. (e.g., because the Gitksan data has an additional segmentation line in IPA).

The data prescreening step will enforce certain formatting expectations, by letting you know of any such issues before you proceed to the segmentation/glossing steps.  Here are those expectations:

1.  **Each sentence has the same number of lines.**  
For example, if you have a 4-line system (transcription, segmentation, gloss, translation), this is the case for every single sentence in your dataset.

2.  **There are no tab characters in the data.**

3.  **There are never multiple consecutive spaces in the data.**

4.  **The segmentation line and gloss lines do not contain multiple consecutive boundaries.**  
That is, morphemes are always connected by either a space or a single boundary character, as in `morpheme1 morpheme2-morpheme3~morpheme4`.  
There is one exception here: infixes in the gloss line, which frequently involve the closing ">" (or "}") boundary immediately followed by any other boundary. See expectation #10 for more details.

5.  **The segmentation line does not contain "hanging" boundaries.**  
That is, morpheme boundaries are always directly connected to a morpheme on either side (e.g., `morpheme1-morpheme2- morpheme3` is *not* permitted).  
This has been seen in cases where a speaker revised what they were saying, or perhaps interrupted themselves, leading to an isolated prefix written as `morpheme-`.  In this case, this should be written as just `morpheme` since it's not attached to anything.  
Again, there's an exception with infixes in the gloss line: since > isn't really indicating a boundary per se, it can occur before a space or EOL.  See expectation #10 for more details about infixes.

6.  **The same boundary types are used between the segmentation and gloss line.**  
For example, consider this segmentation line:  
`morpheme1~morpheme2 morpheme3=morpheme4`  
The corresponding gloss line must look like:  
`gloss1~gloss2 gloss3=gloss4`.

7.  **The segmentation and gloss lines have the same number of words.**  
Words are presumed to be separated by spaces.

8.  **The segmentation and gloss lines have the same number of morphemes.**  
Morphemes can be whole words, or pieces or words separated by morpheme boundaries.  So the total number of morphemes in a line is always >= the number of words.

9.  **Each word has the same number of morphemes in the segmentation and gloss lines.**

10.  **If used, infix boundaries appear in pairs, with only the infixing morpheme in between.  In the segmentation line the infix (with boundaries) of course appears within another morpheme, but in the gloss line it follows that morpheme.**  
This sounds complicated, but it just expects that infixes are formatted in the typical way we've observed.  
Essentially, a word with an infix might be segmented like `start.of.morpheme1<morpheme2>more.morpheme1-morpheme3`, and the corresponding gloss would be `gloss1<gloss2>-gloss3`.  There's really no boundary between gloss2 and gloss3 at all because they're not adjacent, but this format tells us that `gloss2` is an infix on `gloss1`, and `gloss3` regularly attaches to the end of `gloss1`.  Confusing!  But standard, and intelligble.  So with infix boundaries in the gloss line, we expect a morpheme immediately preceding <, and a morpheme boundary or space or EOL immediately following >.

## Boundary System
The only distinction that is fundamentally important when breaking up morphemes is that of infixes vs. regular (linearly-attaching) morphemes.  This is because infixes need to be specially handled to make sure morphemes are correctly identified.  Consider a regular case:  
`morpheme1-morpheme2-morpheme3`  
`gloss1-gloss2-gloss3`  
...versus a word with an infix:  
`start.of.morpheme1<morpheme2>more.morpheme1-morpheme3`  
`gloss1<gloss2>-gloss3`  
As you can see, infixes cause complications.  In the glossing line, we can break things down as usual (because of course no glosses are split).  But in the segmentation line, we have to break things apart carefully if we want to reassemble the underling morphemes (i.e., we have to grab and combine `start.of.morpheme1` and `more.morpheme1` and map them together to `gloss1`, and then get `morpheme2` so that we know it aligns to `gloss2`, etc.)

Examples are in St̓át̓imcets, from Alexander (2016).

### Non-Infixing Boundaries

- regular boundary: -
    - e.g. *s-xát'-su* (gloss: NMLZ-want-SSGP)
- clitic boundary: =
    - e.g. *skalúl7=a* (gloss: owl-EXIS)
- reduplication boundary: ~
    - e.g. *celh~cálh-ts-as* (gloss: TRED-willing+CAUS-FSGO-TE)

### Infixing Boundaries

- regular infix boundaries: <>
    - e.g. *má<7>eg'* (gloss: light-INCH)
- reduplicating infix boundaries: {}
    - e.g. *má{m'}teq* (gloss: walk-CRED)

### A Word on Boundary Directionality
Sometimes the information conveyed by a boundary is directional (i.e., it doesn't apply in the same way to the two morphemes it connects) in a way that isn't recoverable without some external knowledge of how the language works (or analyzing lots of data).

Take our clitic example: *skalúl7=a*.  The boundary tells you that a clitic is attaching -- but which of the two morphemes is the clitic?  Well, based on the length, *a* seems like a much more likely candidate, and we would probably see it recurring elsewhere with =, which probably isn't the case for *skalúl7*.  Or, if you know the language, you'd know the clitic inventory and be able to identify it here.  But the point is, the way the boundaries are used in the segmentation line aren't actually sufficent information on their own to tell what is what.  Note also that the directionality is not consistent -- it's not the case, say, that clitics always go at the end of a word, which would immediately tell us that *a* is the clitic here.  All of this also applies to reduplication boundaries.  Regular boundaries ('-') don't give us any extra info, so we don't have this issue of knowing where to assign that info.

In essence, though reduplication and cliticization are relevant to the *relationship* between two morphemes (one encliticizes onto the other! one is a reduplicant of the other!), this info is much more defining for one morpheme than the other.  With *skalúl7=a*, *skalúl7* is just a stem -- the only perhaps relevant info is that it's the kind of morpheme that can take an enclitic.  But for *a*, it *is* is a clitic.  It will always attach with a clitic boundary.

I think for glossing features we will just encode the previous and following boundaries (incl. end of word boundary) and see if the CRF cares to use this info.

Interestingly, for St̓át̓imcets, the gloss itself for reduplicants seems to just be indicating reduplication and some detail about what kind of reduplication (e.g. CRED, TRED, FRED).  So this glossing style actually makes it clear which part is the redulicant, but this isn't really in line with what the gloss usually conveys (the *meaning* of the morpheme), and we can't assume that other languages' glossing standards work this way.  Indeed, for Nɬeʔkepmxcín, reduplicants are glossed as DIM, AUG, PL, etc.

This isn't the case with infixing boundaries.  Consider a word like *sm'é{m'}lhats=a* (gloss: woman-CRED-EXIS).  It's clear here that *m'* is the infix, whereas *sm'é'lhats* is a normal stem (just one that happens to permit infixes).  In terms of how this translates to features, I think we are breaking this down linearly before giving it to the CRF, so we need to think about how to maintain that boundary information.

## System Summary
### Segmentation
The segmentation works by learning from pairs of unsegmented input data and segmented output data. For example, train.input contains a **list of words**, e.g. "t a o w e n m í n a s".  Then train.output contains the same list of words but with morpheme boundaries, e.g. "t a o w e n - m í n - a s".  So the model goes word-by-word and tries to learn where each word has morpheme boundaries.

The evaluation goes word by word and checks for an exact match. So the word is segmented correctly only if it has each morpheme boundary in the correct position and of the correct type (and hasn't messed up the characters in between).

### Glossing
The glossing model learns from sentences of **segmented** words in the language and the corresponding sentences of **glosses**. It breaks down each sentence into individual morphemes, using the given boundaries.  It **converts each morpheme into a set of features**: currently, this is just the whole morpheme itself, the last 3 characters of the morpheme, the previous morpheme in the sentence, and the following morpheme.  When training, it identifies each morpheme as a stem or gram (based on whether the corresponding gloss is in caps). Stems are just stored in a stem dictionary, and have their gloss replaced with `STEM`. So when the CRF is trained on pairs of features and their gloss, for stems it just learns that they *are* stems, whereas for bound morphemes it learns their gloss. On novel data, the CRF is used to gloss bound morphemes and identify stems, whose gloss is then looked up in the stem dictionary.  If that morpheme isn't in the stem dictionary, then the gloss predictions just gloss it as `STEM` (indicating an unknown stem).

### Pipeline
The pipeline code takes care of translating between the segmentation output and the glossing input.  So essentially it takes the lists of segmented words output by the segmentation model, and **reassembles** those into sentences.  And the glosses it just pulls from the original data like usual.  Then it proceeds with regular glossing!
- At present, the pipeline is doing a check to make sure that **infix boundaries are symmetrical**, i.e. a line contains the same number of "{" as "}" . The simplest approach for now is just to replace any rogue ones with a non-infixing boundary (e.g. `sqwa7>y-án-ak` -> `sqwa7-y-án-ak`), but this will not rememdy a case where the lone infix marker was in fact indicating an infix, and thus treating it as a regular morpheme will lead to a morpheme count mismatch.

## References
Alexander, Qwa7yán’ak Carl, Elliott Callahan, Henry Davis, John Lyon, and Lisa Matthewson. 2016. *Sqwéqwel’ Múta7 Sptakwlh: St’át’imcets Narratives.* Pacific Northwest Languages and Literature Press.
