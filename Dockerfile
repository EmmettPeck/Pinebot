FROM alpine

# Install python/pip
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN apk add --update py-pip

# Install dependencies
RUN pip install python-dotenv
RUN pip install docker
RUN pip install discord
RUN python3 -m pip install "pymongo[srv]"

# Copy Files
ADD .env /
ADD app/ app/

# Start
CMD ["python3", "-u", "app/main.py"]
