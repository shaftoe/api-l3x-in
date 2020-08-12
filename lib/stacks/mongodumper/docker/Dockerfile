FROM debian:buster-slim
RUN apt-get update > /dev/null && \
    apt-get install -q -y --no-install-recommends awscli mongo-tools > /dev/null && \
    apt-get clean
ADD ./mongodumper.sh /usr/local/bin/mongodumper.sh
RUN chmod +x /usr/local/bin/mongodumper.sh
CMD ["mongodumper.sh"]
