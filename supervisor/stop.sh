#!/usr/bin/env bash

ROOT=$(cd `dirname $0`; pwd)
cd $ROOT

kill -3 `cat /tmp/supervisord.pid`
