FROM gcc:9.4.0

RUN apt-get update && \
   apt-get install -y gcc-aarch64-linux-gnu python3 python3-pip make file
RUN apt-get install -y g++-aarch64-linux-gnu
RUN apt-get install -y libmagic-dev
RUN pip3 install --upgrade pip
RUN pip3 install ghidra-bridge
RUN pip3 install python-magic
WORKDIR /app

COPY ./src /app/

RUN chmod -R +x /app

CMD [ "python3", "./CallerGCCver.py" ]