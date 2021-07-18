FROM python:3.8-slim-buster

MAINTAINER madLads

COPY ./requirements.txt /Nucleo/requirements.txt

RUN PIP_DEFAULT_TIMEOUT=100 pip3 install -r /Nucleo/requirements.txt

COPY ./src /Nucleo/src

WORKDIR /Nucleo/src

CMD [ "python3", "-u", "launcher.py" ]
