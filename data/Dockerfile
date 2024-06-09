ARG EXPOSE_PORT=8000

##=============================================================
# https://hub.docker.com/_/node/tags
#FROM node:latest
FROM node:lts-bullseye-slim
#FROM ruby:2.7.4-slim
LABEL maintainer="Akari<masiro.to.akari@gmail.com>"
SHELL ["/bin/bash", "-c"]

##=============================================================
RUN apt update -q
RUN apt install -y build-essential locales zlib1g-dev
#RUN apt install -y procps iputils-ping net-tools dnsutils vim

##=============================================================
RUN apt install -y ruby-full nodejs iproute2

ENV GEM_HOME /root/gems
ENV PATH /root/gems/bin:$PATH

# Gem install
RUN gem install jekyll bundler

##=============================================================
RUN sed -i -e "s/#alias l/alias l/g" /root/.bashrc
RUN sed -i -e "s/# alias l/alias l/g" /root/.bashrc

##=============================================================
WORKDIR /root/jekyll

COPY _config.yml /root/jekyll/_config.yml
RUN sed -i -e 's/\r//g' /root/jekyll/_config.yml

COPY Gemfile /root/jekyll/Gemfile
RUN sed -i -e 's/\r//g' /root/jekyll/Gemfile

##=============================================================
RUN NOKOGIRI_USE_SYSTEM_LIBRARIES=true bundle install

RUN echo "en_US UTF-8" > /etc/locale.gen && locale-gen en-US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8

##=============================================================
COPY entrypoint.sh /root/entrypoint.sh
RUN sed -i -e 's/\r//g' /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh

##=============================================================
EXPOSE $EXPOSE_PORT

##=============================================================
ENTRYPOINT ["/root/entrypoint.sh"]
