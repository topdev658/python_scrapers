#!/usr/bin/env bash

fallocate --length 2GiB /swapfile
# dd if=/dev/zero of=/swapfile bs=2048 count=1000000
mkswap /swapfile
swapon /swapfile
