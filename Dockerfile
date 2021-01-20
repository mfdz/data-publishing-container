FROM python:3.9

WORKDIR /usr/src/app

ENV DPC_MDM_CERT="PATH_TO_CERT:PASSWORD"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Temporary doit patch, see https://github.com/pydoit/doit/issues/381
COPY doit/loader.py /usr/local/lib/python3.9/site-packages/doit

COPY . .

ENTRYPOINT [ "python" ]
CMD [ "/usr/local/bin/doit" ]
