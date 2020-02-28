FROM debian:buster
RUN apt update
RUN apt install -y wget awscli
RUN wget http://kindlegen.s3.amazonaws.com/kindlegen_linux_2.6_i386_v2_9.tar.gz -O kindlegen.tgz
RUN tar xzf kindlegen.tgz -C /usr/local/bin kindlegen
ADD ./kindle_gen.sh /usr/local/bin/kindle_gen.sh
RUN chmod +x /usr/local/bin/kindle_gen.sh

# Remove unneeded packages and files
RUN rm kindlegen.tgz
RUN apt purge -y wget

CMD ["kindle_gen.sh"]
