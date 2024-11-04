# Based on code by Changbing Yang

#!/bin/bash
                                                                            
LAYERS=3 # Good values for morphology
HEADS=4 # ""
FF=1024
EMBED=512
BATCH=128
INTERVAL=4
SEED=$1

SRC=input
TRG=output

DATE=$(date +%Y-%m-%d-%H-%M-%S)
echo $DATE

SAVEDIR=models_seed$SEED
DATADIR=data-bin

[[ ! -d $SAVEDIR ]] &&
echo $SAVEDIR

fairseq-train $DATADIR \
  --source-lang $SRC \
  --target-lang $TRG \
  --save-dir $SAVEDIR \
  --seed $SEED \
  --arch transformer \
  --encoder-layers $LAYERS \
  --decoder-layers $LAYERS \
  --encoder-embed-dim $EMBED \
  --decoder-embed-dim $EMBED \
  --encoder-ffn-embed-dim $FF \
  --decoder-ffn-embed-dim $FF \
  --encoder-attention-heads $HEADS \
  --decoder-attention-heads $HEADS \
  --dropout 0.2 \
  --attention-dropout 0.2 \
  --relu-dropout 0.0 \
  --weight-decay 0.0 \
  --criterion label_smoothed_cross_entropy --label-smoothing 0.2  \
  --optimizer adam --adam-betas '(0.9, 0.98)' \
  --clip-norm 0.0 \
  --lr-scheduler inverse_sqrt \
  --warmup-updates 4000 \
  --warmup-init-lr 1e-7 --lr 0.0005 --stop-min-lr 1e-9 \
  --max-tokens $BATCH \
  --update-freq $INTERVAL \
  --max-epoch 40 \
  --ddp-backend=no_c10d \
  --log-format json --log-interval 20\
  --no-epoch-checkpoints
  ## --save-interval 10 to save checkpoint files at 10, 20, 30, etc. epochs
