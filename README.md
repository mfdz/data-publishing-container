# Data Publishing Container
## YAGNAP - You ain't gonna need another portal

### The problem
Often, organisations which want to publish open data feel a need to first create a "portal" to serve their data. So instead of publishing the data, getting feedback on it, improve it and creating value, they are blocked. Sometimes, building a portal might take years, and no data is published ever (though this should not be the case, as there are prooven open source solutions like CKAN).

The contrary would be to just put the data on the organisations website. This is already the most important step, but usually leads to a couple of issues in the long run:

* Datasets are not found by the intended users, as nobody takes notice of the published datasets
* Datasets a lacking a minimal description which could indicate their fitness for use, let alone a quality assessment
* Datasets are probably published manually, hence always creating a burden on the website administrator and often resulting in infrequent updates

So, just putting data on the organisation's website ignores that the data should meet the [FAIR data](https://www.go-fair.org/) principles: findability, accessibility, interoperability and reusability.

### The solution
We propose a solution which adresses the above cited problems, though being as simple as possible: data publishing containers.
As a data publishing container, we understand a container that at least

* provides an http-server giving access to a folder hierarchy
* every dataset is represented by a folder, containing it's data, metadata, and optionally different representations or validation reports and a datapackage.json which groups these resources.
* every dataset folder serves an index document describing the dataset for humans and  - via a linked data description - for indexing crawlers of search engines as well.


### Beyond the FAIR principles: Commentability and Validatability
Respecting the FAIR principles is already a big step forward for data publishing organisations.
However, I think that too often data quality does not yet meet the user's expectations. This should not hinder organisations from publishing their data, and never be an excuse not to do so. But data quality needs to be addressed: every dataset should be accompanied by a data schema which allows to validate it's structural quality and, if possible, as well with a set of rules describing it's semantical correctnes.

And for issues which can't be detected by automated checks and validations, their should exist a feedback system like almost any software project nowadays has an issue tracker to publicly (at least for open source projects) discuss probable issues.

### Use cases of Data Publishing Containers

This project provides a simple prototype implementation. It demonstrates the following use cases for a Data Publishing Container:

1) Liberation of inaccessible datasets
2) Providing findability for otherwise invisible datasets
3) Validation of datasets (TBD: Integrate results in index page)
4) Providing transformed datasets in a different, probably simpler, schema (TBD)
5) Providing quality improvements for low quality datasets (TBD)
6) Enhancing datasets by combining them with additional data

#### Liberation of inaccessible datasets
The German [Mobilitäts Daten Marktplatz (MDM)]() is a government data portal for (mostly) road traffic related datasets and services. While many datasets in general are available free of charge, accessing them requires multiple registration steps and explicit license confirmation. Using this Data Publihing Container, we liberate them, using a registered account to download them and republish them as accessible datasets.

#### Providing findability for otherwise invisible datasets
Besides liberating datasets from the German Mobilitäts Daten Marktplatz (MDM), we enhance them with linked data metadata, which - though captured by the MDM for every dataset - is not yet published according to the schema.org linked dataset recommendations. By doing so, we make these datasets findable, e.g. via Google Dataset Search.

#### Validation of datasets
Datasets often contain errors. This might be structural errors like format or schema violations which usually are easily detectable and normaly should be handled by the data provider before publishing the data. Harder to detect are semantical errors. They usually require more elaborated check routines, and often additional external context information. 

With this PoC, we provide standard XML schema validation for MDM parking pubications as well as additional schematron checks, which allow to formulate semantic validation rules declarativly. However, as lxml (which we use as schematron validation engine) only supports XPATH1.0, schematron check rules are sometimes hard to understand and algorithmic validation probably would be easier to develop and maintain.  

#### Providing datasets in a simpler schema

TBD. We plan to convert DATEXII Parkdaten datasets into the much simpler ParkAPI format, which already is available for about 30 cities. Other use cases might be: conversion of DATEII MDM Arbeitsstellen data to [Waze's CIFS format](https://developers.google.com/waze/data-feed/feed-setup).

#### Improving dataset quality

TBD

#### Enhancing datasets by combining them with additional data

TBD

## Credits
Many of the ideas cited above are inspired by the way [qri](https://qri.io) handles data: evenry dataset resides in a body file, which is accompanied by a set of metadata files (meta.json and structure.json) which describe the data. On qri.io, every dataset has proper landing page, describing metadata and stats of the dataset. And every dataset has an issue tracker.
qri uses IPFS to distribute datasets, provides version management, sql like query functionality and many features more, so you might want to consider to publish your datasets using qri. Publishing your dataset to qri might be an additonal step in your process chain.

## How to use this project
1) describe the datasets via a dpc.json file
2) if you want to download datasets from MDM, provide path to cert and passwort via environment variable DPC_MDM_CERT


### To run locally on host machine

#### Prerequisites
You need an installed python3 version, probably a new virtual environment (created e.g. via `mkvirtualenv dpc`) and then install dpc's requirements:

```sh
$ pip install -r requirements.txt
``` 

#### Running via local python
 run doit

### To run via docker

#### Prerequisites
You need to have docker installed.

#### Building a docker container
Build a docker container via

```sh
docker build -t mfdz/data-publishing-container .
```

#### Running via docker container
Downloading datasets and generating index pages once:

```sh
docker run --rm --env DPC_MDM_CERT="./certs/mykeyandcerts.pem:mypassword" -v $(PWD)/certs:/usr/src/app/certs -v $(PWD)/out:/usr/src/app/out mfdz/data-publishing-container```
```

Starting a scheduler to check for new data updates every 10 seconds:

```sh
docker run -d --name dpc --env DPC_MDM_CERT="./certs/mykeyandcerts.pem:mypassword" -v $(PWD)/certs:/usr/src/app/certs -v $(PWD)/out:/usr/src/app/out mfdz/data-publishing-container``` dpc.py
```

