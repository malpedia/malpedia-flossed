FROM python:3.10.13-alpine

# upgrade pip
RUN pip install --upgrade pip

# get curl for healthchecks
RUN apk add curl

# permissions and nonroot user for tightened security
RUN adduser -D nonroot
RUN mkdir /home/app/ && chown -R nonroot:nonroot /home/app
RUN mkdir -p /var/log/flossed-falcon && touch /var/log/flossed-falcon/flossed-falcon.err.log && touch /var/log/flossed-falcon/flossed-falcon.out.log
RUN chown -R nonroot:nonroot /var/log/flossed-falcon
WORKDIR /home/app
USER nonroot

# copy all the files to the container
COPY --chown=nonroot:nonroot . .

# venv
ENV VIRTUAL_ENV=/home/app/venv

# python setup
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN export FALCON_APP=main.py
RUN pip install -r requirements.txt

# define the port number the container should expose
EXPOSE 8000

CMD ["python", "main.py"]