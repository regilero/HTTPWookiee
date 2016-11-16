#!/bin/bash
echo 
echo "--- Runing Nginx \"latests\" tests ----"
echo 
export HTTPWOOKIEE_CONF=tests/docker/nginx/latest/config.ini
./httpwookiee.py -V

echo 
echo "--- Runing Nginx \"stable\" tests ----"
echo 
export HTTPWOOKIEE_CONF=tests/docker/nginx/stable/config.ini
./httpwookiee.py -V
