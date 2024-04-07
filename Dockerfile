# Use official Python runtime as a parent image
FROM python:latest

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy only the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the codebase into the container
COPY . /usr/src/app
