#!/usr/bin/env bash


ROOT=$(cd `dirname $0`; pwd)

cd $ROOT

sudo ./stop.sh
sudo ./supervisord.py -c ../../supervisord.conf $@
