FROM debian:jessie
RUN apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install -yq varnish && \ 
        apt-get clean && \
        rm -rf /var/lib/apt/lists
COPY conf/default.vcl /etc/varnish/default.vcl
VOLUME /etc/varnish
VOLUME /var/lib/varnish
EXPOSE 80
ADD start.sh /start.sh
CMD ["/start.sh"]
