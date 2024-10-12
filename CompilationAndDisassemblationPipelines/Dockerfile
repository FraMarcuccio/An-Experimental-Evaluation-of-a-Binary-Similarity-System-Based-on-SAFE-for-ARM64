FROM python:3.9

RUN apt-get update && \
   apt-get install -y gcc-aarch64-linux-gnu python3 python3-pip make file default-jre openjdk-17-jdk
RUN apt-get install -y libmagic-dev
RUN pip3 install --upgrade pip
RUN pip3 install ghidra-bridge
RUN pip3 install python-magic
RUN pip3 install networkx tabulate
WORKDIR /app

COPY ./src2 /app/

RUN chmod -R +x /app

CMD [ "python3", "Caller2.py" ]