FROM python:3.6

RUN pip install pipenv
RUN mkdir /code
WORKDIR /code
ADD . /code
RUN pipenv install --dev --python /usr/local/bin/python
RUN ["chmod", "+x", "/code/invsvc.sh"]
CMD ["/code/invsvc.sh"]
