FROM yuxio/flask-python351

RUN chmod -R 777 /usr/src/app/data
RUN rm /usr/src/app/data/data.db
RUN rm /usr/src/app/data/sources/*
RUN rm /usr/src/app/data/tmp/*

COPY conf/flask.conf /etc/nginx/sites-available/
RUN rm /etc/nginx/sites-enabled/flask.conf
RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf


