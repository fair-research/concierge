from flask import jsonify, make_response, send_from_directory,request, render_template, abort
import uuid
import datetime
from app import app
import json
import boto3
import os
#from encode2bag import encode2bag_api as e2b
from bdbag import bdbag_api as bdbag
from minid_client import minid_client_api as minid_client


def upload_to_s3(filename, key):
    s3 = boto3.resource('s3', aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])
    data = open(filename, 'rb')
    s3.Bucket(app.config['BUCKET_NAME']).put_object(Key=key, Body=data)


@app.route('/bag', methods=['POST'])
def bag():

    query, metadata, ro_manifest = None, None, True

    if "q" in request.json:
        query = request.json["q"]
    if "m" in request.json:
        metadata = request.json["m"]
    if "ro" in request.json:
        ro_manifest = request.json["ro"]

    print ("Request: Q: %s; M: %s; RO: %s" % (query, metadata, ro_manifest))

    key = str(uuid.uuid4())

    try:
        if metadata is not None:
            print ("Creating from metadata file")
            tmp_file = str(uuid.uuid4())
            with open("/tmp/bag_tmp/%s" % tmp_file, 'w') as f:
                f.write(json.dumps(metadata))
            bag_name = "/tmp/bag_tmp/%s" % key
            print('BAG NAME IS %s' % bag_name)
            os.mkdir(bag_name)
            bdbag.make_bag(bag_name,
                           algs=['md5', 'sha256'],
                           metadata={'Creator-Name': 'Encode2BDBag Service'},
                           remote_file_manifest="/tmp/bag_tmp/%s" % tmp_file
            )
            bdbag.archive_bag(bag_name, 'zip')


    except Exception as e:
        #print ("Exception creating bag %s" %e)
        #return "Error creating Bag: %s" %e, 404
        raise

    upload_to_s3("/tmp/bag_tmp/%s.zip" % key, "%s.zip" % key)

    response_dict = {"uri" : "https://s3.amazonaws.com/%s/%s.zip" % (app.config['BUCKET_NAME'], key)}

    if app.config['CREATE_MINID']:
        #print "Creating Minid"
        checksum = minid_client.compute_checksum("/tmp/bag_tmp/%s.zip" % key)
        minid = minid_client.register_entity(app.config['MINID_SERVER'],
                checksum,
                app.config['MINID_EMAIL'],
                app.config['MINID_CODE'],
                ["https://s3.amazonaws.com/%s/%s.zip" % (app.config['BUCKET_NAME'], key)],
                "ENCODE BDBag",
                app.config['MINID_TEST'])

        response_dict["minid"] = minid

    response_dict["globus_uri"] = app.config['GLOBUS_FILE']
    return jsonify(response_dict), 200
