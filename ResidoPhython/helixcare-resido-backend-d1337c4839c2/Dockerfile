# The first instruction is what image we want to base our container on
# We Use an official Python runtime as a parent image
FROM python:3.10

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

# create root directory for our project in the container
RUN mkdir /resido_dev

# Set the working directory to /helix_dev
WORKDIR /resido_dev

# Copy the current directory contents into the container at /helix_dev
ADD . /resido_dev/

RUN apt-get update && apt-get install -y libgdal-dev
# RUN apt-get install -y wkhtmltopdf
RUN apt-get install -y p7zip-full

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements/dev.txt

RUN python3 -m nltk.downloader stopwords
RUN python3 -m nltk.downloader punkt
RUN python3 -m nltk.downloader punkt_tab

RUN chmod +x /resido_dev/worker-entrypoint.sh
RUN chmod +x /resido_dev/beat-entrypoint.sh
RUN chmod +x /resido_dev/server-entrypoint.sh

# Run server
# CMD python manage.py makemigrations
# CMD python manage.py migrate_schemas
CMD python manage.py makemigrations && python manage.py pulse_migrate_schemas && python manage.py collectstatic --noinput && python3 manage.py create_additional_domain && python manage.py runserver 0.0.0.0:8000
