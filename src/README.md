# Automatic Segmentation and Glossing for Gitksan

## Preprocess and Train the Segmentation Model
sh prepare_seg.sh

## Run the Segmentation Model
sh run_seg.sh

## Run (and Train) the Glossing Model
python3 gloss.py

## Run the Entire Pipeline
This one takes a few minutes.  
cat test_for_pipeline.input | fairseq-interactive --path models/checkpoint_best.pt data-bin > test_for_pipeline_fairseq.output  
python3 pipeline.py 
