#!/bin/bash
set -e
echo "******* Building"
cd 1.4
echo "    *** latest"
docker build -t wookieehaproxy_1_4 .
cd ../1.5
echo "    *** stable"
docker build -t wookieehaproxy_1_5 .
cd ../1.6
echo "    *** debian jessie"
docker build -t wookieehaproxy_1_6 .
cd ..
echo "****** remove old containers"
docker rm -f wrphaproxy_1_4||/bin/true
docker rm -f wrphaproxy_1_5||/bin/true
docker rm -f wrphaproxy_1_6||/bin/true

HOSTIP=`ip -4 addr show scope global dev docker0 | grep inet | awk '{print \$2}' | cut -d / -f 1`

echo "****** test configurations"
docker run -it --rm --name wrphaproxy_1_4-syntax-check  --add-host=dockerhost:${HOSTIP} wookieehaproxy_1_4 haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
docker run -it --rm --name wrphaproxy_1_5-syntax-check  --add-host=dockerhost:${HOSTIP} wookieehaproxy_1_5 haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
docker run -it --rm --name wrphaproxy_1_6-syntax-check  --add-host=dockerhost:${HOSTIP} wookieehaproxy_1_6 haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg

echo "******* Running"
docker run --name wrphaproxy_1_4 --add-host=dockerhost:${HOSTIP} -p 8821:80 -d wookieehaproxy_1_4
docker run --name wrphaproxy_1_5 --add-host=dockerhost:${HOSTIP} -p 8822:80 -d wookieehaproxy_1_5
docker run --name wrphaproxy_1_6 --add-host=dockerhost:${HOSTIP} -p 8823:80 -d wookieehaproxy_1_6
echo "******* docker ps"
docker ps -a
# if you want to edit files in a running docker (for tests, do not forget to getyour copy back in conf dir)
#docker run -i -t --rm --volumes-from wrphaproxy_1_6 --name wookieehaproxyfiles debian /bin/bash
