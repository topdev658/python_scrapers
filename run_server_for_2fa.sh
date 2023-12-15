#!/usr/bin/env bash

ulimit -s unlimited
echo "run 2fa server"
cd /home/context/server_for_2fa
python3 server_for_2fa.py --host 0.0.0.0 --port 8181