FROM python:3.11-slim

RUN apt-get update && \
   apt-get install -y python3 make file libmagic-dev python3-magic clang-15
RUN apt-get install -y gcc-aarch64-linux-gnu
RUN apt-get install -y g++-aarch64-linux-gnu
RUN pip install python-magic

ENV PATH=/usr/lib/llvm-15/bin:$PATH

WORKDIR /app

COPY ./src /app/

# Change the permissions of all files and directories within /app recursively.
RUN chmod -R +x /app

CMD [ "python3", "./CallerCLANGver.py" ]