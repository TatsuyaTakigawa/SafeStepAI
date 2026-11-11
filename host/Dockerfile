FROM php:8.3-apache-bookworm

RUN docker-php-ext-install pdo_mysql \
    && a2enmod headers expires \
    && sed -ri 's!/var/www/html!/var/www/html/host!g' /etc/apache2/sites-available/000-default.conf

WORKDIR /var/www/html
COPY host/ /var/www/html/host/
RUN chown -R www-data:www-data /var/www/html/host \
    && find /var/www/html/host -type d -exec chmod 755 {} \; \
    && find /var/www/html/host -type f -exec chmod 644 {} \;

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD php -r '$s=@fsockopen("127.0.0.1",80); exit($s?0:1);'
