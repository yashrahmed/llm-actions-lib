# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y curl
RUN pip3 install --upgrade pip setuptools

# Create a working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN playwright install-deps 
RUN playwright install

# Copy the application files
COPY . .

# Expose the port the app runs on
EXPOSE 80

# Define the command to run the application
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=80"]
