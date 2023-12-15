#!/usr/bin/env bash

ulimit -s unlimited
echo "run 2fa server"
cd ~/_tes/server_for_2fa
# for http://52.207.27.88/:8181
python3 server_for_2fa.py --host 172.31.33.50 --port 8181