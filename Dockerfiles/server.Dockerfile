# Use an official Python runtime as a parent image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Install necessary system libraries
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0

# Set the working directory to /app
WORKDIR /bouncing_ball

# Copy the current directory contents into the container at /app
COPY server.py /bouncing_ball

# Copy requirements.txt into the container at /app/
COPY requirements.txt /bouncing_ball

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the default port (can be overridden at runtime)
ENV PORT=1234

# Make the port specified in the environment variable available to the world outside this container
EXPOSE $PORT

# # Define environment variable
# ENV NAME World

# Run your_script.py when the container launches
CMD ["python", "./server.py"]
