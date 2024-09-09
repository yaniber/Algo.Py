# Use the official Python 3.11 image as a base
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the PYTHONPATH environment variable
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy the rest of the application code into the container
COPY . .

# Command to keep the container running
CMD ["tail", "-f", "/dev/null"]
