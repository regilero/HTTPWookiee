FROM debian:jessie
RUN apt-get update \
	&& apt-get install --no-install-suggests -y \
		ca-certificates \
                nginx
RUN mkdir -p /usr/share/nginx/html
RUN chown -R www-data /usr/share/nginx
RUN rm /etc/nginx/sites-enabled/*
COPY static/ /usr/share/nginx/html/
COPY conf/ /etc/nginx/sites-enabled/
VOLUME /usr/share/nginx/html
VOLUME /etc/nginx

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
