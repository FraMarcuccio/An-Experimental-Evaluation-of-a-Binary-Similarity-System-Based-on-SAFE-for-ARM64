FROM kernelci/clang-16

RUN apt-get update && \
    apt-get install -y python3 make file libmagic-dev python3-magic
RUN apt-get install -y gcc-aarch64-linux-gnu
RUN apt-get install -y g++-aarch64-linux-gnu

# Sets work directory
WORKDIR /app

COPY ./src /app/

# Change the permissions of all files and directories within /app recursively.
RUN chmod -R +x /app

CMD [ "python3", "./CallerCLANGver.py" ]