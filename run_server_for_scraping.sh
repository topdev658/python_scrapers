#!/usr/bin/env bash

ulimit -s unlimited
cd ~
echo "run server"
python3 server_for_scraping_on_demand.py >> logs/server_start_cronjob.log 2>&1