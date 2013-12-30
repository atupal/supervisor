#!/usr/bin/env bash

ROOT=$(cd `dirname $0`; pwd)
cd $ROOT

kill -9 `cat /tmp/supervisord.pid`
