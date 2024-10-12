FROM clangbuiltlinux/ubuntu:llvm12-latest

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 make file libmagic-dev python3-magic python-magic
RUN apt-get install -y clang-19
RUN apt-get install -y clang
RUN apt-get install -y gcc-aarch64-linux-gnu
RUN apt-get install -y g++-aarch64-linux-gnu

WORKDIR /app

COPY ./src /app/

# Change the permissions of all files and directories within /app recursively.
RUN chmod -R +x /app

CMD [ "python3", "./CallerCLANGver.py" ]