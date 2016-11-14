FROM debian:jessie
RUN apt-get update && \
        DEBIAN_FRONTEND=noninteractive apt-get install --no-install-suggests -y \
                curl && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists
RUN curl -sS https://repo.varnish-cache.org/GPG-key.txt | apt-key add - && \
	echo "deb http://repo.varnish-cache.org/debian/ jessie varnish-4.0" >> /etc/apt/sources.list.d/varnish-cache.list && \
	apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install -yq varnish && \ 
        apt-get clean && \
        rm -rf /var/lib/apt/lists
COPY conf/default.vcl /etc/varnish/default.vcl
VOLUME /etc/varnish
VOLUME /var/lib/varnish
EXPOSE 80
ADD start.sh /start.sh
CMD ["/start.sh"]
