### Description

The Concierge Service provides a method of tracking and transferring remote
files through Globus. Files can be tracked with a variety of manifest formats,
including [BDBags](https://github.com/fair-research/bdbag), [Globus Manifests](https://globusonline.github.io/manifests/overview.html), and [Remote File Manifests](https://github.com/fair-research/bdbag/blob/master/doc/config.md#remote-file-manifest).
Creation of a manifest results in a UUID which can be shared with others and used
to view the collection or transfer it to another Globus Endpoint. 
 
### The Concierge API

Users can install the Python [Concierge Client](https://github.com/fair-research/concierge-cli) or use this API directly.

#### Authorization

This API exclusively uses Globus Auth to authorize requests. There are multiple ways to
obtain a Bearer token and use it with this API.

#### Concierge Scope

Users can request Globus Access tokens for the Concierge API with the following scope:

`https://auth.globus.org/scopes/524361f2-e4a9-4bd0-a3a6-03e365cac8a9/concierge`

#### Auth via Concierge API Frontend

Click the 'Django Login' button to login via Globus Auth. The Concierge Service will
obtain the required token for you and pass it along with each request.

#### Auth via Concierge CLI

Install the Python client to login through your local machine:

```
$ pip install git+https://github.com/fair-research/concierge-cli#egg=concierge_cli
$ cbag login
```

#### Auth via Curl

With the `Authorize` button below, you can explicitly set a Bearer token. Obtain a Bearer token with the following:

```
from fair_research_login import NativeClient  # Install with `pip install fair-research-login`
nc = NativeClient(client_id=<client_id>)  # Create a native app client_id at https://developers.globus.org
nc.login(requested_scopes=<concierge_scope>)  # Request a Concierge Service Access Token
```

Curl commands will be displayed when you click `Try it out` --> `Execute`
