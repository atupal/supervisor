#!/usr/bin/env bash


ROOT=$(cd `dirname $0`; pwd)

cd $ROOT

./stop.sh
./supervisord.py -c ../../supervisord.conf
