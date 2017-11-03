# Concierge Service

Your bags will be handled with care.

The Concierge service takes a set of Search results,
creates a BD Bag, and tracks the location with a Minid.

## Environment Setup

* `git clone https://github.com/globusonline/search2bag`
* `cd search2bag`
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements.txt`

BDBags requires the following:

* `pip install --process-dependency-links git+https://github.com/ini-bdds/bdbag`

## Running the App

### Local

* `python manage.py migrate`
* `python manage.py runserver`

This will start the flask server running on `http://localhost:8000`
