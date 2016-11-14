#!/bin/bash
set -e
echo "******* copying static resources here (yep, Dockerfile hack...)"
cp -ar ../../../httpwookiee/static ./2.4/
cp -ar ../../../httpwookiee/static ./2.2/
echo "******* Building"
cd 2.4
echo "    *** latest"
docker build -t wookieehttpd_24 .
cd ../2.2
echo "    *** stable"
docker build -t wookieehttpd_22 .
cd ..
echo "****** remove old containers"
docker rm -f wrphttpd_24||/bin/true
docker rm -f wrphttpd_22||/bin/true
echo "******* Running"
HOSTIP=`ip -4 addr show scope global dev docker0 | grep inet | awk '{print \$2}' | cut -d / -f 1`
docker run --name wrphttpd_24 --add-host=dockerhost:${HOSTIP} -p 8701:80 -d wookieehttpd_24
docker run --name wrphttpd_22 --add-host=dockerhost:${HOSTIP} -p 8702:80 -d wookieehttpd_22
echo "******* docker ps"
docker ps -a
# if you want to edit files in a running docker (for tests, do not forget to getyour copy back in conf dir)
#docker run -i -t --rm --volumes-from wrphttpd_24 --add-host=dockerhost:${HOSTIP} --name wookieehttpdtest debian /bin/bash
