#!/bin/bash
#
# Title: peccary.sh
# Description: run the peccary heeler application
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
PYTHONPATH=$(pwd); export PYTHONPATH
#
source peccary_docker/venv/bin/activate
python peccary_docker/heeler_app.py
#