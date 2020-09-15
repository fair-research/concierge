## Overview

The Concierge Service provides a method of tracking and transferring remote
files through Globus. Files can be tracked with a variety of manifest formats,
including BDBags, Globus Manifests, and Remote File Manifests.
Creation of a manifest results in a UUID which can be shared with others and used
to view the collection or transfer it to another Globus Endpoint.


### The Concierge API

Users can install the Python Concierge Client or use this API directly.

### Authorization

The Concierge Service service uses Globus Auth API access tokens for authentication.

Users may obtain a scope for this service using the following Globus Scope:

    https://auth.globus.org/scopes/524361f2-e4a9-4bd0-a3a6-03e365cac8a9/concierge
    
The [Globus Auth developer guide](https://docs.globus.org/api/auth/developer-guide/)
shows how to register a new Globus Application for utilizing this service.

### Obtaining Tokens

#### Interactive Service API

The Concierge Service provides an interactive REST API for easily using this service
without writing code or registering a new app. Users can click the "Django Login" button
to authenticate with the API, and the service will automatically pass a token for
each request. This serves as a quick method for becoming familiar with the service.

#### Native Applications

Native applications and should use the Native App flow in Globus Auth to obtain tokens.
The Concierge Client includes helpers for completing the Native App flow, and provides
additional python helpers for scripting. The Concierge Client is under heavy development,
check back often for future updates.

https://github.com/fair-research/concierge-cli

Native applications may also implement a custom auth flow like in the examples
below:

https://github.com/globus/native-app-examples


#### Web Applications

Web applications should use the Authorization Code grant in Globus Auth to obtain tokens.

Many Python Frameworks are supported through 
[Python Social Auth](https://python-social-auth.readthedocs.io/en/latest/intro.html).


### Using Tokens

Tokens need to be passed in the request under the Authorization header. Below is an
example: 

    Authorization: Bearer TOKEN
    
## Terminology

### API Terminology

* resource - a URL addressable part of the API, which can be interacted with using a subset of the GET, POST, PUT, and DELETE HTTP methods.
* document - a representation of data, returned by resources as output and accepted by resources as input. There are several standard document types, and some types include sub-documents.

### Document Formats

The API uses json for all input and output, including error documents.

Note that application/x-www-form-urlencoded is not supported. The body should contain the actual JSON data, not a form encoded version of that data.

## API Examples -- Creating and Transferring a Manifest

The service API can be reached at https://develop.concierge.nick.globuscs.info/.

#### POST /api/manifest/globus_manifest/

* Creates a Globus Manifest, and returns a `manifest_id` which can be later queried and used for transfer.

```
{
  "manifest_items": [
    {
      "source_ref": "globus://ddb59aef-6d04-11e5-ba46-22000b92c6ec/share/godata/file1.txt",
      "dest_path": "tut_ep_1_file1.txt",
      "checksum": {
              "algorithm": "md5",
              "value": "5bbf5a52328e7439ae6e719dfe712200"
          }
    },
    {
      "source_ref": "globus://ddb59af0-6d04-11e5-ba46-22000b92c6ec/share/godata/file1.txt",
      "dest_path": "tut_ep_2_file1.txt"
    }
  ]
}
```

Response:

```
201 Created
Content-Type: application/json

{
  "manifest_id": "dc5e17d1-5cfd-48ad-8cdd-ee1eb0c72551",
  "user": "nickolaussaint@globusid.org",
  "manifest_items": [
    {
      "source_ref": "globus://ddb59aef-6d04-11e5-ba46-22000b92c6ec/share/godata/file1.txt",
      "dest_path": "tut_ep_1_file1.txt",
      "checksum": {
        "algorithm": "md5",
        "value": "5bbf5a52328e7439ae6e719dfe712200"
      }
    },
    {
      "source_ref": "globus://ddb59af0-6d04-11e5-ba46-22000b92c6ec/share/godata/file1.txt",
      "dest_path": "tut_ep_2_file1.txt"
    }
  ]
}
```

#### POST /api/manifest/{manifest_id}/transfer/

* Transfer an existing `manifest_id` to a Globus Endpoint.

```
{
  "destination": "globus://ddb59af0-6d04-11e5-ba46-22000b92c6ec/~/my_files"
}
```

```
201 Created
Content-Type: application/json

{
  "manifest_id": "dc5e17d1-5cfd-48ad-8cdd-ee1eb0c72551",
  "manifest_transfer_id": "72b22f76-fc5c-40bc-abd8-9d747158e0ef",
  "user": "nickolaussaint@globusid.org",
  "status": "ACTIVE",
  "transfers": [
    {
      "task_id": "bb549bcc-f799-11ea-abce-0213fe609573",
      "submission_id": "bb549bcd-f799-11ea-abce-0213fe609573",
      "start_time": "2020-09-15T21:23:43.610782Z",
      "completion_time": null,
      "source_endpoint_id": "ddb59aef-6d04-11e5-ba46-22000b92c6ec",
      "source_endpoint_display_name": "Globus Tutorial Endpoint 1",
      "destination_endpoint_id": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
      "destination_endpoint_display_name": "Globus Tutorial Endpoint 2",
      "files": 0,
      "directories": 0,
      "effective_bytes_per_second": 0,
      "bytes_transferred": 0,
      "status": "ACTIVE",
    },
    {
      "task_id": "bb578fe4-f799-11ea-abce-0213fe609573",
      "submission_id": "bb578fe5-f799-11ea-abce-0213fe609573",
      "start_time": "2020-09-15T21:23:43.621060Z",
      "completion_time": "2020-09-15T21:23:45Z",
      "source_endpoint_id": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
      "source_endpoint_display_name": "Globus Tutorial Endpoint 2",
      "destination_endpoint_id": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
      "destination_endpoint_display_name": "Globus Tutorial Endpoint 2",
      "files": 1,
      "directories": 0,
      "effective_bytes_per_second": 3,
      "bytes_transferred": 4,
      "status": "SUCCEEDED",
    }
  ]
}
```

#### GET /manifest/{manifest_id}/transfer/{manifest_transfer_id}/

* Get the current state of the manifest transfer. The manifest may contain multiple 
    transfers if the manifest contained multiple sources. 


```
{
  "manifest_id": "05cc3754-1ce2-46ea-8d15-4fffad119690",
  "manifest_transfer_id": "067f0ed0-9be9-484d-b2ff-eaf36d8e797f",
  "user": "nickolaussaint@globusid.org",
  "status": "SUCCEEDED",
  "transfers": [
    {
      "task_id": "b281302a-f771-11ea-8929-0a5521ff3f4b",
      "submission_id": "b281302b-f771-11ea-8929-0a5521ff3f4b",
      "start_time": "2020-09-15T16:37:09.743331Z",
      "completion_time": "2020-09-15T16:37:12Z",
      "source_endpoint_id": "ddb59aef-6d04-11e5-ba46-22000b92c6ec",
      "source_endpoint_display_name": "Globus Tutorial Endpoint 1",
      "destination_endpoint_id": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
      "destination_endpoint_display_name": "Globus Tutorial Endpoint 2",
      "files": 1,
      "directories": 0,
      "effective_bytes_per_second": 2,
      "bytes_transferred": 4,
      "status": "SUCCEEDED",
    },
    {
      "task_id": "b30123d2-f771-11ea-8929-0a5521ff3f4b",
      "submission_id": "b30123d3-f771-11ea-8929-0a5521ff3f4b",
      "start_time": "2020-09-15T16:37:09.752507Z",
      "completion_time": "2020-09-15T16:37:11Z",
      "source_endpoint_id": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
      "source_endpoint_display_name": "Globus Tutorial Endpoint 2",
      "destination_endpoint_id": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
      "destination_endpoint_display_name": "Globus Tutorial Endpoint 2",
      "files": 1,
      "directories": 0,
      "effective_bytes_per_second": 3,
      "bytes_transferred": 4,
      "status": "SUCCEEDED",
    }
  ]
}
```
