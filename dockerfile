# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot.py and other necessary files to the container
COPY bot.py .

# Expose the port the bot will use (if applicable)
EXPOSE 8080

# Set the command to run the bot
CMD ["python", "bot.py"]