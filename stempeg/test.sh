parallel -j 1 --bar CUDA_VISIBLE_DEVICES=0 python train.py \
  --root /mnt/disks/tdb/tdbva \
  --model-output gs://umx-pro-results/umx-pro-lr{1}-wd{2} \
  --log-output gs://umx-pro-logs \
  --dataset custom \
  --log-steps 500 \
  --batch-size 16 \
  --targets vocals \
  --sources vocals other \
  --seed 42 \
  --augmentations gain \
  --nb-parallel-calls 1 \
  --lr-decay-patience 20000 \
  --patience 20000 \
  --statistics-steps 500 \
  --hidden-size 1024 \
  --steps 20000 \
  --lr {1} \
  --weight-decay {2} \
  ::: 0.001 0.004 0.008 0.012 0.016 0.020 \
  ::: 0.00001 \