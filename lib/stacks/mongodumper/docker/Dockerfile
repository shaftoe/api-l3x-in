FROM debian:buster-slim
RUN apt-get update > /dev/null
RUN apt-get install -y awscli mongo-tools > /dev/null
ADD ./mongodumper.sh /usr/local/bin/mongodumper.sh
RUN chmod +x /usr/local/bin/mongodumper.sh
CMD ["mongodumper.sh"]
