import os
from flask import jsonify, request, render_template_string

from app import app
from api.utils import create_bag_archive, create_minid, upload_to_s3

@app.route('/')
def index():
    message = \
        '<h2>Welcome to Search2Bag</h2>' \
        '<p>See <a href="https://github.com/globusonline/search2bag">here</a>'\
        ' for documentation.</p>'
    return render_template_string(message), 200

@app.route('/bag', methods=['POST'])
def bag():

    remote_files_manifest = request.json.get('remote_files_manifest')
    minid_user = request.json.get('minid_user')
    minid_email = request.json.get('minid_email')
    minid_title = request.json.get('minid_title')
    minid_test = request.json.get('minid_test', False)


    if not remote_files_manifest:
        return 'Invalid Arguments', 400

    try:
        bag_filename = create_bag_archive(remote_files_manifest)
    except Exception as e:
        print ("Exception creating bag %s" %e)
        return "Error creating Bag: %s" %e, 500

    s3_bag_filename = os.path.basename(bag_filename)
    upload_to_s3(bag_filename, s3_bag_filename)

    response_dict = {"uri" : "https://s3.amazonaws.com/%s/%s" % (app.config['BUCKET_NAME'], s3_bag_filename)}

    if app.config['CREATE_MINID']:
        response_dict["minid"] = create_minid(bag_filename,
                                              s3_bag_filename,
                                              minid_user,
                                              minid_email,
                                              minid_title,
                                              minid_test)
    os.remove(bag_filename)

    response_dict["globus_uri"] = app.config['GLOBUS_FILE']
    return jsonify(response_dict), 200
