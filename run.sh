export OMP_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES=0
# python -u main_hyperparams.py > log/log_1125_myself_lstm 2>&1 &
python -u main_hyperparams.py > log_save/log_1125_myself_lst
