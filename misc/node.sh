# Single use rfam render node example for a sun grid engine cluster, to be handed to qsub. This involves setting the prenode cmd parameter to something like: ssh cluster "qsub -t 1-%i node.sh", noting you will have to escape (backslash) the quotes in the json config file and arrange ssh keys so no password is required.
#$ -l h_vmem=6G
#$ -l tmem=6G
#$ -l h_rt=14400
#$ -j y
#$ -S /bin/bash
#$ -o log.txt

umask 002
cd /SAN/vr/3dami/cluster/node/
/opt/python/bin/python3.3 run.py
