# Northern Interior Glossing
This repo provides tools for working with glossed data. This includes:
- scripts for tidying glossed data (checking for inconsistencies, repairing inconsistencies, providing a summary of the data, etc.)
- tools for creating a system to automatically gloss language data.
    - Specifically, the system takes in **unsegmented** language data, as input, and creates a **glossed** output (with a **segmented** version as an intermediate output). That is, the system learns to both **segment** (breaking down language data into its morphemes) and to **gloss** (providing a meaning for each of those morphemes).

Though the tools are intended to be language-general, the system was developed to automate glossing for the three Northern Interior Salish languages -- nɬeʔkepmxcín, St'át'imcets, and Secwepemctsín.  The motivation is to accelerate the language documentation process, leading to more efficient production of glossed texts in these languages, useful to learners and linguists alike.  Because of the small amount of glossed data available for training, the project also employed strategies for cross-lingual learning (learning from related languages).

If you're interested in (some of) the datasets prepared for this project, please see the [StatimcetsGlossedData](https://github.com/anna-stacey/StatimcetsGlossedData) and [nle7kepmxcinGlossedData](https://github.com/anna-stacey/nle7kepmxcinGlossedData) repositories.  You can check out the READMEs inside [data/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/data) and [src/](https://github.com/anna-stacey/NorthernInteriorGlossing/tree/main/src) here for more info on the data and scripts, respectively.

## Citation
This work comprised an M.A. thesis (Stacey, 2025) at UBC Linguistics supervised by Miikka Silfverberg, and funded in part by a CGS-M grant from the Social Sciences and Humanities Research Council (SSHRC) of Canada.  The data component of this project was presented at LREC 2026 (Stacey, 2026).  As such, the most up-to-date citation for the glossed data components -- scripts for tidying and checking the data, expectations/rules for the glossed data to follow, etc. -- is as follows:
> Stacey, Anna. 2026. Glossed Data in Northern Interior Salish. In Proceedings of the Fifteenth Language Resources and Evaluation Conference (LREC 2026) (pp. 3490–3495). European Language Resources Association (ELRA). https://doi.org/10.63317/2isngefy6ags

Meanwhile, for the machine learning side of the project (i.e., training and testing on the data once it is prepared), the thesis itself may be cited:
> Stacey, Anna. 2025. Automatic glossing for Northern Interior languages featuring cross-lingual enhancements. M.A. thesis, University of British Columbia. https://dx.doi.org/10.14288/1.0449331

Please see these two linked documents for more details -- the thesis document covers the broader project in detail, while the LREC Proceedings paper is much more succinct and covers only the data and relevant processes.

## References
Alexander, Carl. 2016. *Sqwéqwel’ múta7 sptakwlh: St̓át̓imcets Narratives by Qwa7yán’ak (Carl Alexander)*. Recorded, transcribed, translated and edited by Elliott Callahan, Henry Davis, John Lyon & Lisa Matthewson. Vancouver and Lillooet, Canada: University of British Columbia Occasional Papers in Linguistics and the Upper St’át’imc Language, Culture and Education Society (USLCES).
