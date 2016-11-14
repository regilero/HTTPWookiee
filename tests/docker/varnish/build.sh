#!/bin/bash
set -e
echo "******* Building"
cd 3.0.6
echo "    *** 3.0.6"
docker build -t wookieevarnish_306 .
cd ../3.0.7
echo "    *** 3.0.7"
docker build -t wookieevarnish_307 .
cd ../debianjessie
echo "    *** debianjessie"
docker build -t wookieevarnish_jessie .
cd ../4.0
echo "    *** 4.0"
docker build -t wookieevarnish_40 .
cd ../4.1
echo "    *** 4.1"
docker build -t wookieevarnish_41 .
cd ..
echo "****** remove old containers"
docker rm -f wrpvarnish_306||/bin/true
docker rm -f wrpvarnish_307||/bin/true
docker rm -f wrpvarnish_jessie||/bin/true
docker rm -f wrpvarnish_40||/bin/true
docker rm -f wrpvarnish_41||/bin/true

HOSTIP=`ip -4 addr show scope global dev docker0 | grep inet | awk '{print \$2}' | cut -d / -f 1`

echo "******* Running"
docker run --name wrpvarnish_306 --add-host=dockerhost:${HOSTIP} -p 8621:80 -d wookieevarnish_306
docker run --name wrpvarnish_307 --add-host=dockerhost:${HOSTIP} -p 8624:80 -d wookieevarnish_307
docker run --name wrpvarnish_jessie --add-host=dockerhost:${HOSTIP} -p 8625:80 -d wookieevarnish_jessie
docker run --name wrpvarnish_40 --add-host=dockerhost:${HOSTIP} -p 8622:80 -d wookieevarnish_40
docker run --name wrpvarnish_41 --add-host=dockerhost:${HOSTIP} -p 8623:80 -d wookieevarnish_41
echo "******* docker ps"
docker ps -a
# to debug a container, use this:
# docker rm -f wrpvarnish_307
# docker run --name wrpvarnish_307 --add-host=dockerhost:${HOSTIP} -p 8624:80 -rm -it wookieevarnish_307 /bin/bash
