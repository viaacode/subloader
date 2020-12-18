# Subloader

## Synopsis
Upload form for subtitles as collateral for mediaobject. Searches
by pid. Shows flowplayer with subtitles after you upload a valid srt.
Subtitle srt is converted to webvtt for pre-viewing in flowplayer.
Finally submit to mediahaven (show confirmation dialog if a srt is already linked).
Allows basically to upload both closed and open srt files to videos for 'testbeeld' tenant
(tenant is now only one but can be easily extended for multiple tenants).

## Prerequisites

* Git
* Docker
* Python 3.6+
* Linux (if you want to run it locally, uwsgi is not available on other platforms.)
* Access to the meemoo PyPi

## Usage

1. Clone this repository with:

    `$ git clone https://github.com/viaacode/subloader.git`

2. Change into the new directory.

### Running locally

1. Start by installing pip packages and setting up environment:
    `scripts/install`

2. Activate the virtual environment:

    `$ source python_env/bin/activate`

4. Run the tests with:

    `$ scripts/test`

5. Run the application:

   `$ scrits/run`

The application is now serving requests on `localhost:8080`. Try it with:

    `$ curl -v -X GET http://127.0.0.1:8080/`

### Running using Docker

1. Build the container and run it:

   `$ scripts/build`

### Helper scripts
To run the tests locally and also run flake8 linter/code checking:
```
$ scripts/test    
================================ test session starts =================================
platform darwin -- Python 3.8.5, pytest-5.4.1, py-1.10.0, pluggy-0.13.1 
cachedir: .pytest_cache
rootdir: /Users/wschrep/FreelanceWork/VIAA/subloader
plugins: recording-0.11.0, cov-2.8.1
collected 25 items                                                                   

tests/test_app.py::test_home PASSED                                            [  4%]
tests/test_app.py::test_liveness_check PASSED                                  [  8%]
tests/test_app.py::test_search_media_security PASSED                           [ 12%]
tests/test_app.py::test_search_media PASSED                                    [ 16%]
tests/test_app.py::test_invalid_pid_entry PASSED                               [ 20%]
tests/test_app.py::test_empty_pid PASSED                                       [ 24%]
tests/test_app.py::test_wrong_pid_entry PASSED                                 [ 28%]
tests/test_app.py::test_working_pid_search PASSED                              [ 32%]
tests/test_app.py::test_bad_srt_upload PASSED                                  [ 36%]
tests/test_app.py::test_invalid_upload PASSED                                  [ 40%]
tests/test_app.py::test_empty_upload PASSED                                    [ 44%]
tests/test_app.py::test_valid_subtitle PASSED                                  [ 48%]
tests/test_app.py::test_valid_subtitle_capitals PASSED                         [ 52%]
tests/test_app.py::test_cancel_upload PASSED                                   [ 56%]
tests/test_app.py::test_subtitle_videoplayer_route PASSED                      [ 60%]
tests/test_app.py::test_subtitle_videoplayer_route_unknownfile PASSED          [ 64%]
tests/test_app.py::test_send_to_mam_shows_confirmation PASSED                  [ 68%]
tests/test_app.py::test_send_to_mam_confirm_works PASSED                       [ 72%]
tests/test_app.py::test_send_to_mam_cancel_works PASSED                        [ 76%]
tests/test_app.py::test_random_404 PASSED                                      [ 80%]
tests/test_authorization.py::test_jwt PASSED                                   [ 84%]
tests/test_authorization.py::test_bad_jwt PASSED                               [ 88%]
tests/test_authorization.py::test_token_signature_bad_decode PASSED            [ 92%]
tests/test_authorization.py::test_wrong_credentials PASSED                     [ 96%]
tests/test_authorization.py::test_right_credentials PASSED                     [100%]

================================= 25 passed in 1.63s =================================
Running flake8 linter...
ALL OK
```
If you get flake8 warnings during development there's a scripts/autopep command you can run
that will auto-fix most styling issues (basically a python equivalent to rubocop -a used in ruby projects).


Test coverage report can be generated with following script/coverage:

```
$ scripts/coverage
================================ test session starts =================================
platform darwin -- Python 3.8.5, pytest-5.4.1, py-1.10.0, pluggy-0.13.1
rootdir: /Users/wschrep/FreelanceWork/VIAA/subloader
plugins: recording-0.11.0, cov-2.8.1
collected 25 items                                                                   

tests/test_app.py ....................                                         [ 80%]
tests/test_authorization.py .....                                              [100%]

---------- coverage: platform darwin, python 3.8.5-final-0 -----------
Name                    Stmts   Miss  Cover
-------------------------------------------
app/__init__.py             0      0   100%
app/authorization.py       44      7    84%
app/config.py              19      0   100%
app/mediahaven_api.py      51      4    92%
app/subloader.py          142      3    98%
app/subtitle_files.py      71      3    96%
app/validation.py          21      3    86%
-------------------------------------------
TOTAL                     348     20    94%
Coverage HTML written to dir htmlcov


================================= 25 passed in 1.92s =================================
```


### Environment variables

Best set following environment variables before running the server. This
allows login to work and also makes the mediahaven calls to upload the srt and lookup
metadata by pid functional:

```
export MEDIAHAVEN_API=https://archief-qas.viaa.be/mediahaven-rest-api
export MEDIAHAVEN_USER= lookup in team pass
export MEDIAHAVEN_PASS= lookup in team pass

export OAS_SERVER=https://oas-qas.viaa.be
export OAS_APPNAME=mediahaven

export FLOWPLAYER_TOKEN= lookup or ask Bart or Walter for this token
```

For production deploys you also set the OAS_JWT_SECRET (see last section on verification of bearer token). Flowplayer token is also needed to be able to preview the subtitles in the flow player (on dev/localhost it works without token,but once deployed you need it to not get an error from the player).
This env var is exposed to javascript code starting flowplayer in app/templates/preview.html


### Running the server locally:

To run a server on port 8080:

```
$ scripts/run
```
The root page is login screen for configured oas server.

following this link <a href="http://127.0.0.1:8080/">Subloader</a> after you have the server running.


During development you can autoformat using scripts/autopep and to make changes and see response instantly without restarting the application
theres the scripts/debug helper script now
```
$ scripts/debug
```
It also runs on port 8080 like the scripts/run and docker builds



### Verification of bearer token

In order to verify bearer token the secret key is shared. This is base64 encode hs256 jwt key. We share the key as environment variable OAS_JWT_SECRET
and it is stored here for qas: https://do-prd-okp-m0.do.viaa.be:8443/console/project/public-api/browse/secrets/avo-oas-qas-develop-config
and here for prd: https://do-prd-okp-m0.do.viaa.be:8443/console/project/public-api/browse/secrets/avo-oas-prd-master-config.

The k value for the respective environment is stored in OAS_JWT_SECRET and the syncrator-api decodes + verifies the jwt signature from OAS in the verify_token method in app/authorization.py we also verify the audience == 'syncrator' this is the 'aud' in the jwt token. When signature verification is enabled this verifies also the audience and throws an exception if it does not match (which is caught and results in a 401 access denied). Without the OAS_JWT_SECRET a fallback mode decodes the jwt token and checks the 'aud' value but this is unsecure and therefore a warning message will be printed to setup the secret properly.


