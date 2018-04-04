# Concierge Service

Your bags will be handled with care.

The Concierge service creates, tracks, and stages transfers of BDBags
referencing each with a Minid.

## Usage

#### Example: Creating a bag

You can create a bag with the following POST request to `https://example.com/api/bags/`

Header: `Authorization: Bearer <globus_auth_token>`

JSON Payload:

    {
      "minid_user": "Malcolm Reynolds",
      "minid_email": "captainreynolds@globus.org",
      "minid_title": "concierge-test",
      "remote_files_manifest":
        [
            {
                "url":"globus://ddb59aef-6d04-11e5-ba46-22000b92c6ec:/share/godata/file1.txt",
                "length": 4,
                "filename": "file1.txt",
                "md5": "5bbf5a52328e7439ae6e719dfe712200",
                "sha256": "2c8b08da5ce60398e1f19af0e5dccc744df274b826abe585eaba68c525434806"
            }
        ]
    }

The above will create a BDBag, assign it a minid, and upload the BDBag to an Amazon S3
Server. An example response is below:

    {
        "id": 5,
        "url": "http://example.com/api/bags/5/",
        "minid_id": "ark:/99999/fk43f5zk6m",
        "minid_email": "captainreynolds@globus.org",
        "location": "https://s3.amazonaws.com/my-s3/bdbag.zip"
    }

## Running the server locally

* `git clone https://github.com/fair-research/concierge`
* `cd concierge`
* `virtualenv venv`
* `source venv/bin/activate`
* `pip install -r requirements.txt`
* `python manage.py migrate`
* `python manage.py runserver`

This will start the server running on `http://localhost:8000`
