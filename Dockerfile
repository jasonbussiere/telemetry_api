#lightweight base image
FROM python:3.14-slim

#set working directory
WORKDIR /app

#prevent python from writing useless .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
#forces Python to stream all text instantly ensuring real-time updated logs
ENV PYTHONUNBUFFED=1

#copy requirements.txt
COPY requirements.txt .

#install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


#copy the rest of the application code
COPY . .

# Expose the port the API listens on
EXPOSE 5000

# Command to start the API
CMD ["flask", "run", "--host=0.0.0.0"]