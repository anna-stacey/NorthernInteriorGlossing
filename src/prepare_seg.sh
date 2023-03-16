# Prepare the data for fairseq
python3 preprocess_seg.py  
fairseq-preprocess --source-lang input --target-lang output --trainpref train --validpref dev --destdir data-bin/
# Train fairseq
sh train_seg.sh 