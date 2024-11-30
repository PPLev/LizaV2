FROM python:3.12-slim

WORKDIR /app
ENV APP_ROOT=/app/src

RUN apt-get update && \
    apt-get install --no-install-recommends -y git gcc build-essential portaudio19-dev

RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN echo "Europe/Moscow" > /etc/timezone

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt && chmod 755 .

COPY . ${APP_ROOT}

WORKDIR ${APP_ROOT}