FROM python:3-alpine

WORKDIR /usr/src/hyundai_kia_connect_monitor
COPY ./hyundai_kia_connect_monitor/* ./
COPY ca-certificates.crt mqtt_utils.py ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "paho_mqtt>=2.0"
ENV HOME=/usr/src
ENTRYPOINT [ "python", "-u", "./monitor.py" ]

