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
click **Install** over the app you wish to install, found among the ones available for you under the
[App Store](https://sfbicycles.gorgias.com/app/apps).

Clicking the **Install** button will ensure two things:

1. The app is fully updated and prepared for the flow on our end.
2. The app initialization finalizes with a redirect into the _App URL_ you provided during the app creation in the
   [Developer Portal](https://gorgias-portal.openchannel.site/app/create).
   
Keep in mind that the _App URL_ field needs to contain `{gorgias_account}` (in path or as a query parameter), so you
know where to authorize it and further do API requests. (as the very same app can be installed in multiple accounts)

Example of _App URL_: `https://your-app-back-end.com/install?account={gorgias_account}` (Gorgias will redirect here
when you press **Install** -- which translates into something like
`GET https://sfbicycles.gorgias.com/app/apps/60925f8fe90ded5e265acdf1?install=true` ->
`GET https://your-app-back-end.com/install?account=sfbicycles`)

After this is configured in the Portal, and the route available in your back-end, you can continue with the flow as
described below.


### App authorization

The installation route pointed above should trigger on your side a GET call into Gorgias' `/oauth/authorize` endpoint
with a redirect URL pointing to your callback route.

```bash
curl -i -u <user>:<password> -X GET "https://sfbicycles.gorgias.com/oauth/authorize?\
response_type=code&\
client_id=60925f8fe90ded5e265acdf1&\
scope=openid+email+profile+offline+write:all&\
redirect_uri=https://gorgias-app-flask-cosmin.herokuapp.com/oauth/callback?account=sfbicycles&\
state=XZXZV2dXvFudpo8HTaL7cPwGJxr4XS&\
nonce=0327tRehleepX9gcgA7O"
```

`<user>:<password>` means you have to be authenticated before authorizing the app. 

###### Parameters

- `client_id`: The same as the app ID.
- `scope`: Permissions the app require for completing the flow. (confirmed in the authorization page -- for now the app
  gets access to all resources available to the user authorizing it)
    - `openid`, `email`, `profile`: populates the ID token with user info
    - `offline`: enables access token refreshing
    - `write:all`: write access into all resources
- `redirect_uri`: Where to redirect (on the app's back-end) after the app is authorized in order to get the tokens.
  Make sure to have this URL among your _Redirect URLs_ configured in the Portal.
- `state`: Random string, protecting against CSRF attacks.
- `nonce`: Random string, binds it with the token, so we identify the original request that issued it.

A permissions consent screen will be displayed and if you accept them you'll be redirected into the `redirect_uri` with
a `code` parameter and the very same `state` you provided. Through `state` you can verify if the request coming here
was  originally triggered by you.

```bash
HTTP/1.1 302 FOUND
Content-Type: text/html; charset=utf-8
Date: Wed, 12 May 2021 19:08:59 GMT
Location: https://gorgias-app-flask-cosmin.herokuapp.com/oauth/callback?account=sfbicycles&code=ruu5ebEeAcdxSYrbR7T65xpFhA6fo99O98xX9wlRhqnFehj6&state=XZXZV2dXvFudpo8HTaL7cPwGJxr4XS
Server: nginx/1.14.0
Content-Length: 0
```


### Getting the tokens

For retrieving the tokens you need to make a POST call into Gorgias' `/oauth/token` endpoint with the `code` received
during the authorization step. During this step you need to authenticate the request with the app credentials.

```bash
curl -u 60925f8fe90ded5e265acdf1:cosmin-remote-demo -X POST https://sfbicycles.gorgias.com/oauth/token \
  -d grant_type=authorization_code \
  -d redirect_uri="https://gorgias-app-flask-cosmin.herokuapp.com/oauth/callback?account=sfbicycles" \
  -d code=ruu5ebEeAcdxSYrbR7T65xpFhA6fo99O98xX9wlRhqnFehj6
```

App credentials are simply `<client_id>:<client_secret>`.

- `client_id`: The same as the app ID.
- `client_secret`: Generated in the Developer Portal.

###### Parameters

- `redirect_uri`: The very same redirect URL you used during the authorization step.
- `code`: The code you received after successfully authorizing the app.

You'll get a JSON response containing the `access_token` and `refresh_token`.

```json
{
    "access_token":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjB6NWZweTZ5MjhVbUVXaDdyUlZxSG1oNzdpRks1OERLbXhRMkdIWTUySk0ifQ.eyJpc3MiOiJodHRwczovL2FjbWUtY21pbi5uZ3Jvay5pbyIsInN1YiI6MTAsImF1ZCI6Imh0dHBzOi8vYWNtZS1jbWluLm5ncm9rLmlvL2FwaSIsImlhdCI6MTYyMDg0NjQ4MSwiZXhwIjoxNjIwOTMyODgxLCJhenAiOiI2MDkyNWY4ZmU5MGRlZDVlMjY1YWNkZjEiLCJqdGkiOiJiUHVmMEZQNiIsInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUgb2ZmbGluZSB3cml0ZTphbGwifQ.ZjChPxJoENjTYh7Y7rx-i-ukYRms61x4HCu28q6vWX5Ts7vwVwRkEqRMzWh88_EwSYvBALhBnPlcv9P0Piks-YIi0sqFgegnhIZmIhuqUMH3oaWC3BYX3eKo_JekuqmtJ7Q84mfgL_ZvNJwcK6wB-LIGGxhW-98X8uOqrjGEqRu00-nlcUlsJak56RLGH75C4M_waC6a1KjHEtPHI_D62xFAAJu5H8bRdnVOkTEGYXne9lGpvNg9p7gaeKxh1Fs6q3yY3POqlAnC3p7YjoUV-yli3j_vXw2BiCV340U5IV9beRRgxDxfmRAzxtCav-d88gnBh24ty7P4gddEejjHtg",
    "expires_in":0,
    "id_token":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjbWUtY21pbi5uZ3Jvay5pbyIsImF1ZCI6WyI2MDkyNWY4ZmU5MGRlZDVlMjY1YWNkZjEiXSwiaWF0IjoxNjIwODQ3MDA5LCJleHAiOjE2MjA5MzM0MDksImF1dGhfdGltZSI6MTYyMDg0Njk1OCwibm9uY2UiOiIwMzI3dFJlaGxlZXBYOWdjZ0E3TzExMSIsImF0X2hhc2giOiJzX3RUVFA3OU9yNUJzOHJnMndUZFVRIiwic3ViIjoxMCwibmFtZSI6IkNvc21pbiBQb2llYW5hIiwiZW1haWwiOiJjb3NtaW5AYWNtZS5nb3JnaWFzLmlvIn0.v7Hl0iULirBC5UpxeoHpPFuEMLcZKz6IrR8xrLFIcLdT6LB-20u1UPei2ZlpO4ZoyojIglJNKYc1oPYHk1FExa9CKSJGw-dsQVumqNXP7Xk4AwN9PYYIOhyJHA37eRqsbGiLWzMDS4QknZ-OPnrgMFUSSDF1bhyQRqrXiVLOGmESOMJNUd5xKiaQ3a9t7tWdu3IB7Y8sx9UwYC8VOqZSzE3Zihn0Ydg6_xQ9u9ocLKK7bIar7r3aYADUVwBkAzB7J59QN0RZxVnEAtDQZFqViEK0gImWaWpDOMQBPRNpkm3VFZCQYY50qJAA9Pb53XRdvkCyC6R06vYiawgkNUjd4g",
    "refresh_token":"Bn8nh9P76uDYZb6wADnV93CyuiqaKaaI00mXQpWFWjfbBR06",
    "scope":"openid email profile offline write:all",
    "token_type":"Bearer"
}
```

- `access_token` can be used with the `Authorization: Bearer <token>` header in order to make authorized Gorgias API
  requests.
- `refresh_token` will be used for issuing new access tokens once the one you use expires.


#### Issuing new access token

The received `access_token` is valid for 24h only, afterwards you need to issue a new one using the non-expiring
`refresh_token`.

```bash
curl -i -u 60925f8fe90ded5e265acdf1:cosmin-remote-demo -X POST https://sfbicycles.gorgias.com/oauth/token \
  -d grant_type=refresh_token \
  -d refresh_token=Bn8nh9P76uDYZb6wADnV93CyuiqaKaaI00mXQpWFWjfbBR06
```

```json
{
    "access_token":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjB6NWZweTZ5MjhVbUVXaDdyUlZxSG1oNzdpRks1OERLbXhRMkdIWTUySk0ifQ.eyJpc3MiOiJodHRwczovL2FjbWUtY21pbi5uZ3Jvay5pbyIsInN1YiI6MTAsImF1ZCI6Imh0dHBzOi8vYWNtZS1jbWluLm5ncm9rLmlvL2FwaSIsImlhdCI6MTYyMDg0NzI2OSwiZXhwIjoxNjIwOTMzNjY5LCJhenAiOiI2MDkyNWY4ZmU5MGRlZDVlMjY1YWNkZjEiLCJqdGkiOiJNTVl5ZnhqWSIsInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUgb2ZmbGluZSB3cml0ZTphbGwifQ.gztT0VP10vNdHCSLIuFkj3OTGOt6a0onVs_441ajlwxjYVSWL1_rq4yFoybNz2mNIr8RbWn5LeRVSV5Cw3eiTIE_9F0W47tyapTaAMJ5M7mMI9hdHrz_pNr0nWWIAIGdMDXW6--P46itcC4Qa8VbV305-WkfXKIQ7BnFt9hb-WHN_bnILDR6R3hbvFZIjnw8fFw1_QDnT4TzW4m_t7z4Of1Kea3TB4TZg-0vHKVVsZAqkqK1oPtE3ItnxgT-_dt5iwdGp4q2Dr1G0ANpciYDYOy3Sc83OEg-hX-DvvnZMnBW6E8GceyF9wQ_kjVGnfe4DYnnSCKQImkK3ERcvC0y4w",
    "expires_in":0,
    "scope":"openid email profile offline write:all",
    "token_type":"Bearer"
}
```

The token is actually a stateless signed JWT, you can decode its content with a tool like [jwt.io](https://jwt.io/):

```json
{
  "iss": "https://sfbicycles.gorgias.com",
  "sub": 10,
  "aud": "https://sfbicycles.gorgias.com/api",
  "iat": 1620847269,
  "exp": 1620933669,
  "azp": "60925f8fe90ded5e265acdf1",
  "jti": "MMYyfxjY",
  "scope": "openid email profile offline write:all"
}
```


#### Revoking the refresh token (uninstalling the app)

You can cut the access of the app by pressing the **Uninstall** button or by manually revoking the
`refresh_token`. Note that the app will still have access until the current access token expires. We can't control this
since the token is a stateless JWT.

```bash
curl -i -u 60925f8fe90ded5e265acdf1:cosmin-remote-demo -X POST https://sfbicycles.gorgias.com/oauth/revoke \
  -d token=Bn8nh9P76uDYZb6wADnV93CyuiqaKaaI00mXQpWFWjfbBR06
```

```bash
HTTP/1.1 200 OK
Content-Length: 2
Cache-Control: no-store
Content-Type: application/json
Date: Wed, 12 May 2021 19:27:57 GMT
Pragma: no-cache
Server: nginx/1.14.0
X-Frame-Options: Deny

{}
```

Now if you want to refresh the token again you'll get `{"error": "invalid_grant"}`. Once the `access_token` expires,
the app won't be able to access Gorgias API anymore nor issue new access tokens for accessing it. The app has to be
re-installed for regaining access.


### Caveats

- OAuth2 enhanced security: PKCE layer isn't enabled yet (`code_challenge`, `code_verifier`)
- App Store is currently enabled for a few test accounts in production, please file a support ticket for enabling it
  into your `<account>.gorgias.com` as well.


### References

- External App Store demo app [repo](https://github.com/gorgias/appstore-demo-app)
