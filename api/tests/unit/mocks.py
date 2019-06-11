import os

FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
TEST_BAG = os.path.join(FILES_DIR, 'testbag.zip')

MOCK_TOKENS = {
    'identifiers.globus.org': {
        'access_token': 'identifiers_access_token'
    }
}

MOCK_IDENTIFIERS_GET_RESPONSE = {
  "admins": [
    "urn:globus:auth:identity:37c89679-d62b-4ff8-a24f-80bbfe7eed57",
    "urn:globus:auth:identity:4846deda-625e-4456-9c84-1647e53d71e1",
    "urn:globus:auth:identity:b5614711-228d-414f-8092-b518a25b072f",
    "urn:globus:auth:identity:3b843349-4d4d-4ef3-916d-2a465f9740a9",
    "urn:globus:auth:identity:94f0c387-9528-4bed-b373-4ad840f32661",
    "urn:globus:groups:id:23acce4c-733f-11e8-a40d-0e847f194132"
  ],
  "checksums": [
    {
      "function": "sha256",
      "value": "3e39e3ebd01a65ddf2d44f7124ddb471c62687b0caee3eaf5f6bfc4927a76795"
    }
  ],
  "identifier": "ark:/99999/fk4Q8Vm1Bcm7QYM",
  "landing_page": "https://identifiers.globus.org/ark:/99999/fk4Q8Vm1Bcm7QYM",
  "location": [
    "https://s3.amazonaws.com/fair-research-concierge/bags/84d4d476-2e8b-4cb8-bda7-094b654bbd86/Concierge-Bag-June-11-2019.zip"
  ],
  "metadata": {},
  "visible_to": [
    "public"
  ]
}