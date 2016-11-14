#!/bin/bash
exec /usr/sbin/varnishd -F -a :80 -f /etc/varnish/default.vcl -s malloc,128m -S /etc/varnish/secret
