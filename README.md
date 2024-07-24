# Automatic Glossing
This repo provides a system that can be trained to automatically gloss langauge data.  There are two sub-tasks it will learn: segmentation (breaking down language data into its morphemes) and glossing (providing a meaning for each of those morphemes).  Though the final target output is the gloss, the segmentation process is also performed so that you can begin with just regular, unsegmented langauge data as input.
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
You must provide glossed data in the language that you intend the model to learn to gloss.  Most of this data will be used for training (train), with some reserved for a separate round of improvements (development), and others still saved for evaluation, if so desired (test).  Thus, the system expects to find a train, dev, and test file to work with.

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

## Boundary System
We use an inventory of several symbols to indicate different kinds of morpheme boundaries.  These are the boundaries the system expects to recognize and handle.  There is nonetheless some flexibility in how closely your data must share the same boundaries.  
You can:
- *Not* use some of the boundaries.  If some of these boundary types simply never occur in your data, that's absolutely fine.  But make sure you don't use them for another purpose, because they will get recognized as a boundary by the system.
- Use some of the boundaries for a different purpose.  As discussed more below, the only crucial differences is between infixing and non-infixing boundaries, but within these groups, the purpose of a boundary is not set in stone.  So, for example, if '=' is used in your data, but to indicate a lexical suffix rather than a clitic, that's totally fine.

But, you cannot:
- Use other symbols for morpheme boundaries.  The system will not be able to recognize them as such.
- Use one of our non-infixing boundaries for infixes, or one of our infixing boundaries for non-infixes.  Because these two classes of boundaries are handled differently in the code, they cannot be swapped about at will.

With that out of the way, here are the boundaries that the system handles and we use in our data.  Examples are in St̓át̓imcets, from Alexander (2016).

#### Non-Infixing Boundaries

- regular boundary: -
    - e.g. *s-xát'-su* (gloss: NMLZ-want-SSGP)
- clitic boundary: =
    - e.g. *skalúl7=a* (gloss: owl-EXIS)
- reduplication boundary: ~
    - e.g. *celh~cálh-ts-as* (gloss: TRED-willing+CAUS-FSGO-TE)

#### Infixing Boundaries

- regular infix boundaries: <>
    - e.g. *má<7>eg'* (gloss: light-INCH)
- reduplicating infix boundaries: {}
    - e.g. *má{m'}teq* (gloss: walk-CRED)

Finally, a word on non-infixing vs. infixing boundaries.  The only distinction that is fundamentally important when breaking up morphemes is that of infixes vs. regular (linearly-attaching) morphemes.  This is because infixes need to be specially handled to make sure morphemes are correctly identified.  Consider a regular case:  
`morpheme1-morpheme2-morpheme3`  
`gloss1-gloss2-gloss3`  
...versus a word with an infix:  
`start.of.morpheme1<morpheme2>more.morpheme1-morpheme3`  
`gloss1<gloss2>-gloss3`  
As you can see, infixes cause complications.  In the glossing line, we can break things down as usual (because of course no glosses are split).  But in the segmentation line, we have to break things apart carefully if we want to reassemble the underling morphemes (i.e., we have to grab and combine `start.of.morpheme1` and `more.morpheme1` and map them together to `gloss1`, and then get `morpheme2` so that we know it aligns to `gloss2`, etc.)


### A Word on Boundary Directionality
Sometimes the information conveyed by a boundary is directional (i.e., it doesn't apply in the same way to the two morphemes it connects) in a way that isn't recoverable without some external knowledge of how the language works (or analyzing lots of data).

Take our clitic example: *skalúl7=a*.  The boundary tells you that a clitic is attaching -- but which of the two morphemes is the clitic?  Well, based on the length, *a* seems like a much more likely candidate, and we would probably see it recurring elsewhere with =, which probably isn't the case for *skalúl7*.  Or maybe the capitalization of their respective glosses tells you that *a* is a gram and *skalúl7* is a clitic, making you pretty sure that *a* is indeed the clitic.   Or, if you know the language, you'd know the clitic inventory and be able to identify it here.  But the point is, the way the boundaries are used in the segmentation line aren't actually sufficent information on their own to tell what is what.  Note also that the directionality is not consistent -- it's not the case, say, that clitics always go at the end of a word, which would immediately tell us that *a* is the clitic here.  All of this also applies to reduplication boundaries.  Regular boundaries ('-') don't give us any extra info, so we don't have this issue of knowing where to assign that info.

In essence, though reduplication and cliticization are relevant to the *relationship* between two morphemes (one encliticizes onto the other! one is a reduplicant of the other!), this info is much more defining for one morpheme than the other.  With *skalúl7=a*, *skalúl7* is just a stem, which, sure, a clitic can attach to.  But for *a*, it *is* a clitic.  It will always attach with a clitic boundary.

[I think for glossing features we will just encode the previous and following boundaries (incl. end of word boundary) and see if the CRF cares to use this info.]

Interestingly, for St̓át̓imcets, the gloss itself for reduplicants seems to just be indicating reduplication and some detail about what kind of reduplication (e.g. CRED, TRED, FRED).  So this glossing style actually makes it clear which part is the redulicant, but this isn't really in line with what the gloss usually conveys (the *meaning* of the morpheme), and we can't assume that other languages' glossing standards work this way.  Indeed, for Nɬeʔkepmxcín, reduplicants are glossed as DIM, AUG, PL, etc.

This isn't the case with infixing boundaries.  Consider a word like *sm'é{m'}lhats=a* (gloss: woman-CRED-EXIS).  It's clear here that *m'* is the infix, whereas *sm'é'lhats* is a normal stem (just one that happens to permit infixes).  In terms of how this translates to features, I think we are breaking this down linearly before giving it to the CRF, so we need to think about how to maintain that boundary information.


## Brackets
Many fieldworkers use some system of brackets to indicate material that is only present underlyingly.  However, the details of this practice vary along several parameters:
1. What is the purpose of the brackets? What are they conveying about the bracketed material?
2. What kind of brackets are used? e.g., [] () {}
4. In which lines does the bracketed *content* appear?
3. In which of the lines specified in (3) do the *brackets* appear?
5. In the case of whole morphemes bracketed, does the morpheme boundary go in or out of the brackets? i.e., [-t] vs -[t]

Information about the standards used in the datasets developed alongside this system are available in the READMEs for those repositories.  Generally, however, we standardized the data to:
- only use [] (no other bracket types, i.e., no parentheses)
- include the bracketed content in the segmentation and gloss lines, but *not* the transcription line
- only include the brackets themselves in the segmentation line
- write the morpheme boundary *outside* of the brackets
These expectations are included in the list [below](#data-expectations).

An example from St̓át̓imcets is provided here (Alexander, 2016):  
> nílh t'u7 sawenítas i smúlhatsa kástskacw  
nílh t'u7 [s]=saw-en-ítas i smúlhats=a kás-ts=kacw  
COP EXCL NMLZ=ask-DIR-TPle PL.DET woman=EXIS how-CAUS=2SG.SBJ  
So they asked the women, ``How did you do it?''

The way this is handled by the system is as follows.  The segmentation goes word-by-word, so the brackets cause no fuss -- it just gets the input/output pair *sawenítas* and *[s]=saw-en-ítas*.  Then, the glossing stage flat out removes all brackets from its input before going morpheme-by-morpheme, so it would get the input/output pair *s* and *NMLZ*.  That is, the glosser is entirely oblivious to the brackets.

The user is therefore not entirely beholdent to these standards.  For example, if you also put the brackets in the transcription line, it would not cause any problems, it would just affect the input the segmentation model sees.  However, there are some potential problems if you deviate: for example, if you used parentheses instead of brackets, the gloss line would not remove them and so would be trying to gloss a morpheme like *(s)* rather than *s*, which it may not know what to do with.

## Data Expectations
There are certain expectations in place about the format of data inputted to the system, so that it knows how to handle the different lines.  In preparing data for this system, we had to confront many decisons about what data should look like.  Often, there are many reasonable possibilities, but nonetheless one must be selected for the sake of consistency.  Below is a compiled list of these expectations.  
There are two kinds of expectations:
- Some, like separating words with single spaces (never tabs), are just a matter of making the data computer-friendly, and need not be heeded in everyday glossing practices.  A simple script could be used to convert your data into a format that follows these rules.  
- However, other expectations are more general best practices for glossing, relevant outside just this project.  For example, using a special boundary to mark reduplication (~), or marking stress in the same spot across the transcription and segmentation lines.  In many such cases, you may have a different practice -- and indeed, it may be just as reasonable (as long as you are consistent about it!).  In order to have clean, consistent data, we simply had to make *a* choice on these matters and commit to it.
- ...and some expectations fall into both of these categories!

We have sorted the expectations below according to these categories, to make it clearer which must be *absolutely* followed to have the system handle your data, and which are just guidelines.

#### Expectations which are simply necessary for this system to handle your data, but are not general glossing guidelines:
1.  **Each sentence has the same number of lines.**  
For example, if you have a 4-line system (transcription, segmentation, gloss, translation), this is the case for every single sentence in your dataset.  
Typical exceptions to this are the inclusion of English comments from the speaker, with just one line.  These should be removed before inputting the data.

2.  **There are no tab characters in the data.**

3.  **There are never multiple consecutive spaces in the data.**

4. **The transcription, segmentation, and gloss lines do not contain any punctuation (besides special characters).**
This certainly may be untrue for the data as published in a book, as the text needs to be readable and will typically use standard punctuation as part of this.  However, this punctuation should be removed as part of prepping the data for the model.  This is for the simple reason that punctuation is irrelevent for segmentation/glossing and should not be included in the input or output of these processes.  
Things like commas, exclamation points, question marks, quotation marks, etc. should be removed (and are rarely used in the gloss line, anyways).  The following are the exceptions, and are permitted:  
- in the transcription/segmentation/gloss lines: asterisks, only as outlined in (5)
- in the segmentation/gloss lines: morpheme boundaries: - = ~ <> {}
    - note that there is no obligation to make use of all of these boundary types, but any instances of - = ~ will be treated as a non-infixing morpheme boundary and any instances of <> {} will be treated as infixing morpheme boundaries
- in the gloss line: periods, where they are used in multiword glosses (e.g., bake.bread)  
One final note is that we have seen (e.g., in Gitksan data) '???' used in the segmentation line for unknown morphemes.  Instead, we have changed these unknown morphemes to a) just the same as the transcription line in the segmentation line and b) UNK (= unknown) in the gloss line.  

5. **Asterisks can be optionally used to mark words that are not in the target language (e.g., English words, onomatopoeia) which should be ignored by the system.  If so, the word must be consistent across the transcription/segmentation/gloss lines: it must begin with an asterisk in all three, and have an identical form in all three.**  
For example, if you use the word Vancouver but want it to be ignored, it should appear as `*Vancouver` in the transcription, segmentation, *and* gloss lines.  Even the capitalization must be consistent.  
The purpose of this is so that users have a way to communicate to the system to ignore certain words -- if you want to input a sentence that has, say, a person's name, you want the system to ignore it, not try to segment and gloss it!  At this stage, there is the added benefit of removing these words from training (so as not to feed the language-specific systems what is essentially garbage), and not evaluating on them (so we are more accurately evaluating on the target language).

6. **Brackets for indicating underlying material are square brackets only.**  
No parentheses, and {} will be recognized as morpheme boundaries.

#### Expectations which are necessary for the system *and* are general glossing recommendations:
7.  **The transcription, segmentation and gloss lines have the same number of words.**  
Words are presumed to be separated by spaces. In some practices, clitics are an exception to this (i.e., clitics may be written as indepdenent words in the transcription line, but written as attached morphemes in the segmentation and gloss lines).  Nonetheless even these clitics must be made consistent across lines before the data can be inputted (we just changed them to be separate words in all lines in our dataset, as we believed it preferable to not alter the transcription line).

8.  **The segmentation and gloss lines have the same number of morphemes.**  
Morphemes can be whole words, or pieces or words separated by morpheme boundaries.  So the total number of morphemes in a line is always >= the number of words.

9.  **Each word has the same number of morphemes in the segmentation line as it does in the gloss line.**  

10.  **The segmentation and gloss lines do not contain multiple consecutive boundaries.**  
That is, morphemes are always connected by either a space or a single boundary character, as in `morpheme1 morpheme2-morpheme3~morpheme4`.  
There is one exception here: infixes in the gloss line, which frequently involve the closing ">" (or "}") boundary immediately followed by any other boundary. See expectation #10 for more details.

11.  **The segmentation and gloss lines do not contain "hanging" boundaries.**  
That is, morpheme boundaries are always directly connected to a morpheme on either side (e.g., `morpheme1-morpheme2- morpheme3` is *not* permitted).  
This has been seen in cases where a speaker revised what they were saying, or perhaps interrupted themselves, leading to an isolated prefix written as `morpheme-`.  In this case, this should be written as just `morpheme` since it's not attached to anything.  
Again, there's an exception with infixes in the gloss line: since > isn't really indicating a boundary per se, it can occur before a space or EOL.  See expectation #10 for more details about infixes.

12.  **The same boundary types are used between the segmentation and gloss line.**  
For example, consider this segmentation line:  
`morpheme1~morpheme2 morpheme3=morpheme4`  
The corresponding gloss line must look like:  
`gloss1~gloss2 gloss3=gloss4`

13.  **If used, infix boundaries appear in pairs, with only the infixing morpheme in between.  In the segmentation line, the infix (with boundaries) of course appears within another morpheme, but in the gloss line, it follows that morpheme.**  
This sounds complicated, but it just expects that infixes are formatted in the typical way we've observed.  
Essentially, a word with an infix might be segmented like `start.of.morpheme1<morpheme2>more.morpheme1-morpheme3`, and the corresponding gloss would be `gloss1<gloss2>-gloss3`.  There's really no boundary between gloss2 and gloss3 at all because they're not adjacent, but this format tells us that `gloss2` is an infix on `gloss1`, and `gloss3` regularly attaches to the end of `gloss1`.  Confusing!  But standard, and intelligble.  So with infix boundaries in the gloss line, we expect a morpheme immediately preceding <, and a morpheme boundary or space or EOL immediately following >.

14. **Bracketed content (if any) appears in the segmentation and gloss lines, but never the transcription line.**  
If the bracketed content also appeared in the transcription line, then the segmentation line would just be adding brackets, which is not predictable.  In such cases, the content should be left in and the brackets removed.  The addition of whole underlying morphemes in brackets to the segmentation line, however, is predictable.  Check out the brackets section of Stacey (2024) for a thorough explanation of the reasoning on this front.

15. **Brackets themselves only appear in the segmentation line.**  
Including brackets in the transcription line was unattested in our data.  Including brackets in the gloss line wouldn't convey any new information, so we just gloss bracketed morphemes as usual there.  
If you keep brackets in the gloss line, the system will function but it will learn the brackets to be part of the gloss label, likely impacting your performance.

16. **Brackets appear within morpheme boundaries.**  
This decision is fairly arbitrary, but one style of *[-t]* vs. *-[t]* must be chosen, and we went with the latter for handling ease.  If you use the other style, the glosser will still split the morphemes at boundary points, meaning the previous morpheme will end in an opening square bracket.

#### Expectations that are just glossing guidelines, and will not lead to issues with the system if not followed by your data:
17.  **Stress is marked at most one time per word.**  
Multiple stress markers (the acute accent) will be flagged as a mistake.  This will not actually trip up the system, but is considered an error and thus results in noisy data.

18. **Stress marking is consistent (between the transcription and segmentation lines).**  
If stress is marked on a word, then it should be marked on the same place in the segmented version of a word.  Again, this is not a necessity for system functioning, but a standard we selected to prevent conflicting practices in the datasets.  Alternative approaches include not marking any stress in the segmentation line, or marking stress in the segmentation line to reveal some additional information about where stress comes from.  Our rule was chosen based on simplicity and popularity.

## References
Alexander, Qwa7yán’ak Carl, Elliott Callahan, Henry Davis, John Lyon, and Lisa Matthewson. 2016. *Sqwéqwel’ Múta7 Sptakwlh: St’át’imcets Narratives.* Pacific Northwest Languages and Literature Press.
