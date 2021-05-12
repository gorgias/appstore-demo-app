# appstore-demo-app
Gorgias App Store app demo

This is a set of open-source demo apps available in our App Store in order to illustrate some examples of doing the
OAuth2 flow, so the app can receive tokens and access Gorgias API with them.

We have the followings examples:

- Flask [app](Python/Flask/app.py) (Python)


## OAuth2

We implemented this standard authentication protocol into our own auth and identity provider, so in order to authorize
(install) apps in the App Store you need to authenticate with us. For this, we support the _Authorization Code Grant_
which is mainly composed of two steps:

1. Authorizing the app.
2. Retrieving the tokens based on a `code` from step **1**.


### Prerequisites

Before triggering the flow, the app has to be set-upped for OAuth2 on our end. For achieving this you simply need to
click _Install_ over the app you wish to install, found among the ones available for you under the
[App Store](https://gorgias.gorgias.com/app/apps).

Clicking the install button will ensure two things:

1. The app is fully updated and prepared for the flow on our end.
2. The initialization finalizes with a redirect into the **App URL** you provided during the app creation in the
   [Developer Portal](https://gorgias-portal.openchannel.site/app/create).
   
Keep in mind that the App URL needs to contain `{gorgias_account}` (in path or as query parameter) so you know where to
authorize it and further do API requests. (as the very same app can be installed in multiple accounts)

Example: `https://your-app-back-end.com/install?account={gorgias_account}`

After this is configured, and the route available in your back-end, you can continue with the flow as described
below.


### App authorization

The installation route pointed above should trigger a GET call into the `/oauth/authorize` endpoint with a redirect URL
pointing to your callback route.

_ToDo example_

A permissions consent screen will be displayed and if you accept them you'll be redirected into the `redirect_uri` with
a `code` parameter.

_ToDo request JSON example_


### Getting the tokens

For retrieving the tokens you need to make a POST call into the `/oauth/token` endpoint with the `code` received during
the authorization step. During this step you need to authenticate the request based on the app
`client_id:client_secret`.

You'll get a JSON response containing the `access_token` and `refresh_token`.

###### ToDo

- issuing new access tokens
- revoking the refresh token
- caveats: tokens expiring time, install/uninstall, JWT, PKCE, enabled-accounts (test-cosmin) etc.
