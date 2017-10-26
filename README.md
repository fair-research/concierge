# search2bag

Takes a set of Search results, creates a BD Bag, assigns a mini, returns the minid

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

* `./main.py`

This will start the flask server running on `http://localhost:5000`

## REST Endpoints

`/bag`:

* [POST](#bag-post): Create a bag and get the minid


### bag POST

POST with JSON matching the following format. The following example is valid:

    {
        "minid_user": "Firstname Lastname",
        "minid_email": "name@example.org",
        "remote_files_manifest": [
            {
                "url":"https://raw.githubusercontent.com/ini-bdds/bdbag/master/profiles/bdbag-profile.json",
                "length":699,
                "filename":"bdbag-profile.json",
                "md5":"9faccdb6f9a47a10d9a00bd2b13f7ab3",
                "sha256":"eb42cbc9682e953a03fe83c5297093d95eec045e814517a4e891437b9b993139"
            },
            {
                "url":"ark:/88120/r8059v",
                "length": 632860,
                "filename": "minid_v0.1_Nov_2015.pdf",
                "sha256": "cacc1abf711425d3c554277a5989df269cefaa906d27f1aaa72205d30224ed5f"
            }
        ]
    }

Notes about the fields:

* `minid_user`: Is the name of the user, and will show up as the author of the minid/bdbag
* `minid_email`: Is the email of the person creating the bag. Search2Bag will automatically
register the minid by this email if they are not already registered.
* `remote_files_manifest`: These fields will be passed down to bdbag and can be found in more detail [here](https://github.com/ini-bdds/bdbag/blob/master/doc/config.md#remote-file-manifest).
    * `url`: **Required** The URL of the content. Only protocols allowed by bdbag are allowed.
    * `filename`: **Required** The name of the file

You will receive a response in the following format:

    {
        "globus_uri": "https://www.globus.org/app/transfer?origin_id=endpoint_name",
        "minid": "ark:/99999/abcdefg",
        "uri": "https://s3.amazonaws.com/bucket-name/archive-bag-name.zip"
    }
