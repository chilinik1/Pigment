#!/bin/bash
source ~/.venvs/pigment/bin/activate
cd ~/Projects/pigment
PYTHONPATH=src python3 -m pigment.main
