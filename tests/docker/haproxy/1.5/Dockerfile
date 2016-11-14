FROM haproxy:1.5
COPY conf/haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
VOLUME /usr/local/etc/haproxy

EXPOSE 80 1298

CMD ["haproxy", "-f", "/usr/local/etc/haproxy/haproxy.cfg"]
