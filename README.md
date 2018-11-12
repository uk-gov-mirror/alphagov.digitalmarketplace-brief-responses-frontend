# Digital Marketplace brief-responses frontend

[![Build Status](https://travis-ci.org/alphagov/digitalmarketplace-brief-responses-frontend.svg?branch=master)](https://travis-ci.org/alphagov/digitalmarketplace-brief-responses-frontend)
[![Coverage Status](https://coveralls.io/repos/github/alphagov/digitalmarketplace-brief-responses-frontend/badge.svg?branch=master)](https://coveralls.io/github/alphagov/digitalmarketplace-brief-responses-frontend?branch=master)
[![Requirements Status](https://requires.io/github/alphagov/digitalmarketplace-brief-responses-frontend/requirements.svg?branch=master)](https://requires.io/github/alphagov/digitalmarketplace-brief-responses-frontend/requirements/?branch=master)

Frontend brief responses application for the digital marketplace.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Quickstart

Install dependencies, build assets and run the app
```
make run-all
```

Debian (jessie) users will need `libxslt1-dev` and `libxml2-dev` installed for `requirements-dev`.

## Full setup

Create a virtual environment
 ```
 python3 -m venv ./venv
 ```

### Activate the virtual environment

```
source ./venv/bin/activate
```

### Upgrade dependencies

Install new Python dependencies with pip

```make requirements-dev```


## Front-end

Front-end code (both development and production) is compiled using [Node](http://nodejs.org/) and [Gulp](http://gulpjs.com/).

### Requirements

You need Node (try to install the version we use in production -
 see the [base docker image](https://github.com/alphagov/digitalmarketplace-docker-base/blob/master/base.docker)).

To check the version you're running, type:

```
node --version
```

### Installation

[How to install yarn](https://yarnpkg.com/en/docs/install)
To install the required Node modules, type:

```
yarn
```

## Frontend tasks

[YARN](https://yarnpkg.com/en/) is used for all frontend build tasks. The commands available are:

- `yarn run frontend-build:development` (compile the frontend files for development)
- `yarn run frontend-build:production` (compile the frontend files for production)
- `yarn run frontend-build:watch` (watch all frontend files & rebuild when anything changes)





### Run the tests

To run the whole testsuite:

```
make test
```

To test individual parts of the test stack use the `test-flake8`, `test-python`
or `test-javascript` targets.

eg.
```
make test-javascript
```

### Run the development server

To run the briefs responses frontend app for local development use the `run-all` target.
This will install requirements, build assets and run the app.

```
make run-all
```

To just run the application use the `run-app` target.

The brief responses frontend runs on port 5006. Use the app at [http://127.0.0.1:5006/suppliers/opportunities](http://127.0.0.1:5006/suppliers/opportunities)

Note:  The login is located in the buyer frontend application, so this needs to be running as well to login as a supplier.

If the application is running on port 5006 as described above, login from http://127.0.0.1:5002/login (buyer frontend) as a supplier and then you will be logged in as a supplier on http://127.0.0.1:5006/suppliers/opportunities

It is easier to use the apps if nginx is configured to run them through one port.  As described in the Digital Marketplace Manual:

The frontend applications are hyperlinked together but are running on different ports. This can cause links to error when they link between different applications. The way around this is to set up nginx so all front end applications can be accessed through port 80.

To do this use the bootstrap.sh script in the nginx folder from [digitalmarketplace-functional-tests](https://github.com/alphagov/digitalmarketplace-functional-tests) to set up nginx aliases.

In this case all the frontend applications will available from port 80 usually aliased to localhost and the brief responses application can be accessed from [localhost/suppliers/opportunities](localhost/suppliers/opportunities)

### Updating application dependencies

`requirements.txt` file is generated from the `requirements-app.txt` in order to pin
versions of all nested dependecies. If `requirements-app.txt` has been changed (or
we want to update the unpinned nested dependencies) `requirements.txt` should be
regenerated with

```
make freeze-requirements
```

`requirements.txt` should be commited alongside `requirements-app.txt` changes.
