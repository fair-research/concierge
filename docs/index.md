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

Document Formats

The API uses json for all input and output, including error documents.

Note that application/x-www-form-urlencoded is not supported. The body should contain the actual JSON data, not a form encoded version of that data.

Supported resources / api endpoints with examples
Below is a list of the supported resources or api endpoints with example calls. For brevity, the base url is omitted, for example https://manifests.globus.org. Also, the authentication header is also omitted in the request portion.