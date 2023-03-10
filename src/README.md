# Automatic Segmentation and Glossing for Gitksan

## Train the Segmentation Model
The models are already included to prevent you waiting around for them to train.  If you'd like to, however, here are the steps. The value of training epochs can be changed in train_seg.sh to something smaller to avoid long-ish wait times (it takes less than 30 mins on my laptop though).  
python3 preprocess_seg.py  
fairseq-preprocess --source-lang input --target-lang output --trainpref train --validpref dev --destdir data-bin/  
sh train_seg.sh  

## Run the Segmentation Model
This one takes a few minutes.  
cat test.input | fairseq-interactive --path models/checkpoint_best.pt data-bin > test_fairseq.output

And then to evaluate it:  
python3 test_seg.py

## Run (and Train) the Glossing Model
python3 gloss.py

## Run the Entire Pipeline
This one takes a few minutes.  
cat test_for_pipeline.input | fairseq-interactive --path models/checkpoint_best.pt data-bin > test_for_pipeline_fairseq.output  
python3 pipeline.py 
