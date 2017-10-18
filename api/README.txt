Endpoints:

/    -- GET - Receive this message
/bag -- POST - Create a new BDBag (with remote files), create a minid, and store it on S3

Usage:

/bag -- POST
POST with JSON matching the following format. The following example is valid:
{
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
You will receive a response in the following format:
{
    "globus_uri": "https://www.globus.org/app/transfer?origin_id=endpoint_name",
    "minid": "ark:/99999/abcdefg",
    "uri": "https://s3.amazonaws.com/bucket-name/archive-bag-name.zip"
}
