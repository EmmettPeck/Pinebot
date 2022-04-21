FROM python:3
COPY .env /
COPY data/* data/
ADD cogs/* cogs/
ADD *.py /
RUN pip install python-dotenv
RUN pip install docker
RUN pip install discord
CMD python3 /main.py