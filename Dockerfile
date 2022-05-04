FROM alpine

# Install python/pip
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

# Install dependencies
RUN pip install python-dotenv
RUN pip install docker
RUN pip install discord

# Copy Files
ADD .env /
ADD cogs/* cogs/
ADD *.py /

# Start
CMD python3 /main.py