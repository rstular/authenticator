# sample-nginx-auth-request
Python implementation of ngx_http_auth_request_module.

The API exposes 3 endpoints:
 - `/api/auth/verify/<realm>` - direct nginx's authentication requests here. Verifies that the user has a valid cookie for this realm.
 - `/api/auth/login/<realm>` - used by the login frontend. Performs a JSON POST request against the endpoint, assigned to the specific realm (defined in JSON configuration file). The code can be adapted to perform additional permission checks, currently it also contains some custom handling code for GimB authentication endpoint (although this shouldn't prevent it from working with any endpoint).
 - `/api/auth/logout/<realm>` - used by the webpage - for logging the user out. It delets the user's browser cookie and its corresponding entry in redis database.
 
All files for an exapmle setup are available in the repository. To set it up, you probably will have to fiddle around with UNIX permissions of the files, directories and sockets; if you need any help, feel free to open an issue.

If you need any additional support, open an issue as well.
