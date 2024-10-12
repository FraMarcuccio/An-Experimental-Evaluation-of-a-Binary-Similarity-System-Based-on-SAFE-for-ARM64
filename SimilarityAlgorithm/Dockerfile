# Use an official Python 3.10 base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y build-essential 

# Install python3-dev
RUN apt-get install -y python3-dev 

# Install libsqlite3-dev for sqlite3
RUN apt-get install -y libsqlite3-dev 

# Install Capstone
RUN pip install --no-cache-dir capstone

# Install networkx
RUN pip install --no-cache-dir networkx

# Install numpy
RUN pip install --no-cache-dir numpy

# Install pandas
RUN pip install --no-cache-dir pandas

# Install scikit-learn
RUN pip install --no-cache-dir scikit-learn

# Install node2vec
RUN pip install --no-cache-dir node2vec

# Install seaborn
RUN pip install --no-cache-dir seaborn

# Install matplotlib
RUN pip install --no-cache-dir matplotlib

# Install tensorflow
RUN pip install --no-cache-dir tensorflow

# Add the current directory to the container
COPY ./src3 /app/

# Define the default command to run the container
CMD [ "python3", "CallerSim.py" ]