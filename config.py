class Config(object):
    DEBUG = False
    TESTING = False


    AWS_ACCESS_KEY_ID = ""
    AWS_SECRET_ACCESS_KEY = ""
    CREATE_MINID = True
    MINID_SERVER = "http://minid.bd2k.org/minid"
    MINID_EMAIL = ""
    MINID_CODE = ""
    MINID_TEST = False
    MINID_SERVICE_TOKEN = ''
    API_WELCOME_MESSAGE = 'api/README.txt'

    BAG_ARCHIVE_FORMAT = 'zip'

    GLOBUS_FILE = "https://www.globus.org/app/transfer?origin_id=6a84efa0-4a94-11e6-8233-22000b97daec&origin_path=%2Ffdab4915-a1f0-42f1-8579-e1999d0648ca%2F"
    BUCKET_NAME = "portal-sc17-nick-globuscs-info"
