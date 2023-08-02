# St’át’imcets Glossing
## Data
The data comes from *Sqwéqwel’ Múta7 Sptakwlh: St’át’imcets Narratives* by Qwa7yán’ak (Alexander, 2016), and consists of 18 stories:  
### Legends
1. *Ta skalúl7a múta7 ta smém̓lhatsa* / The Owl and the Girl
2. *Mulhatswíl'c i smelhmém'lhatsa* / When Girls Become Women  
### History  
3. *Ta a7x7ánwasa kúkwa7* / The Resourceful Grandmother  
4. *Ićin'as i kel7ás t'iq i sám7a* / Long Ago When White People First Came  
### Growing Up at Nqwáxwqten  
5. *Na kél7a áts'xenan sw'úw'a* / The First Cougar I Saw  
6. *Cwepqám'ku ákwal'micw* / Digging for Cedar Roots  
7. *Na kél7a nspíxem'* / The First Time I Went Hunting  
### Residential School Experiences  
8. *Ta skwátsitsa na nsqátsez7a lhláku7 ta xzúma ntsunám'calten* / My Father's Name from the Residential School  
9. *I kel7án tsicw ta xzúma tsunám'calten* / When I First Went to Residential School  
10. *I t'iqmin'tsálemas ta Indian Agent-a* / When the Indian Agent Came for Me
### Later Life and Work  
11. *I kel7án úts'qa7 lhélta xzúma tsunám'calten* / When I First Left Residential School  
12. *I ns7al7á7el'ksta* / All My Little Bits of Work  
13. *I zet'q'án7an lta xzúma sxetq* / When the Side of the Big Hole Caved in on Me  
14. *'A7xa7 i ts'ánts'en'a* / Grasshoppers are Powerful  
15. *Cw7aoz aylh lhkúnsa kw nskaxékcala* / I Can't Count Anymore  
16. *Na pél'pa nqatsk* / My Lost Older Brother  
### Reflections  
17. *Ta tsuwa7lhkálha nqwal'útten múta7 nt'ákmen* / Our Own Language and Traditional Ways
18. *Ta xzúma tmícwlhkalh* / Our Big Land

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
