FROM nginx:stable
COPY static/ /usr/share/nginx/html/
COPY conf/ /etc/nginx/conf.d/
RUN rm /etc/nginx/conf.d/default.conf
VOLUME /usr/share/nginx/html
VOLUME /etc/nginx
