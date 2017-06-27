FROM python:3.5

# Install pip requirements
COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Define working directory and copy files to it
RUN mkdir /code
WORKDIR /code
COPY . /code/

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["python", "crawl.py"]
