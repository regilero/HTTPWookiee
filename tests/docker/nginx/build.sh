#!/bin/bash
set -e
echo "******* copying static resources here (yep, Dockerfile hack...)"
cp -ar ../../../httpwookiee/static ./latest/
cp -ar ../../../httpwookiee/static ./stable/
cp -ar ../../../httpwookiee/static ./debianjessie/
echo "******* Building"
cd latest
echo "    *** latest"
docker build -t wookieenginx_latest .
cd ../stable
echo "    *** stable"
docker build -t wookieenginx_stable .
cd ../debianjessie
echo "    *** debian jessie"
docker build -t wookieenginx_jessie .
cd ..
echo "****** remove old containers"
docker rm -f wrpnginx_latest||/bin/true
docker rm -f wrpnginx_stable||/bin/true
docker rm -f wrpnginx_jessie||/bin/true
echo "******* Running"
HOSTIP=`ip -4 addr show scope global dev docker0 | grep inet | awk '{print \$2}' | cut -d / -f 1`
docker run --name wrpnginx_latest --add-host=dockerhost:${HOSTIP} -p 8801:80 -d wookieenginx_latest
docker run --name wrpnginx_stable --add-host=dockerhost:${HOSTIP} -p 8802:80 -d wookieenginx_stable
docker run --name wrpnginx_jessie --add-host=dockerhost:${HOSTIP} -p 8803:80 -d wookieenginx_jessie
echo "******* docker ps"
docker ps -a
# if you want to edit files in a running docker (for tests, do not forget to getyour copy back in conf dir)
#docker run -i -t --rm --volumes-from wrpnginx_latest --name wookieenginxfiles debian /bin/bash
