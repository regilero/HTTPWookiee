FROM httpd:2.4.23
COPY static/ /usr/local/apache2/htdocs/
COPY conf/httpd.conf /usr/local/apache2/conf/httpd.conf
COPY conf/extra/httpd-vhosts.conf /usr/local/apache2/conf/extra/httpd-vhosts.conf
COPY conf/extra/httpd-mpm.conf /usr/local/apache2/conf/extra/httpd-mpm.conf
COPY conf/extra/httpd-default.conf /usr/local/apache2/conf/extra/httpd-default.conf
RUN chown -R www-data /usr/local/apache2/htdocs/*
VOLUME /usr/local/apache2/conf
VOLUME /usr/local/apache2/htdocs/
EXPOSE 80
CMD ["httpd-foreground"]
