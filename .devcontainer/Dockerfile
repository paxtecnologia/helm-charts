FROM alpine/helm:latest

ARG USER=dev-user
ARG USER_ID=1000

RUN apk add --update \
  sudo \
  git \
  curl \
  openssh

# add dev-user
RUN addgroup -S $USER \
  && adduser -S $USER -G $USER -u $USER_ID -s /bin/ash \
  && echo "$USER ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/$USER \
  && chmod 0440 /etc/sudoers.d/$USER