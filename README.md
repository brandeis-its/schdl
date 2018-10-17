# Setting up Schdl

These directions assume a brand new VM running on Google Compute Engine with
Ubuntu 18.04 LTS. To enable deploying to App Engine, the VM should be
configured under "Cloud API access scopes" to "Allow full access to all Cloud
APIs."

## Initial setup

```shell
sudo apt-get update
git clone https://github.com/emosenkis/schdl
cd schdl
./setup.sh
```

## Enter the dev environment (do this every time you want to build

```shell
cd $HOME/schdl
. schdl.env
. venv/bin/activate
```

## Create a new school entry in the database

```shell
bin/addSchool.py --fragment testu --name Test\ University --email_domain test.com --website test.com --hostname 127.0.0.1
bin/ensureIndices.py
```

## Copy the following into `~/schdl/gae/app.yaml`

```yaml
runtime: python
env: flex

runtime_config:
    python_version: 2

entrypoint: gunicorn -c gunicorn.conf.py -b :$PORT schdl.wsgi:app

env_variables:
    FLASK_MAIL_SERVER: 'MAIL_SERVER'
    FLASK_MAIL_PORT: 'MAIL_PORT'
    FLASK_MAIL_USE_TLS: 'MAIL_TLS_ENABLED'
    FLASK_MAIL_PASSWORD: 'PASSWORD'
    FLASK_MAIL_USERNAME: 'USERNAME'
    FLASK_MAIL_SENDER: 'MAIL_SENDER'
    FLASK_SECRET_KEY: 'SECRET'
    SCHDL_DB_URI: 'MONGODB_URI'
    SCHDL_GCS_BUCKET: 'GCS_BUCKET'
    SCHDL_EMAIL_ERRORS_TO: 'ERRORS_EMAIL'

skip_files:
    - ^\.git/.*
    - ^venv/.*

automatic_scaling:
    min_num_instances: 2
    max_num_instances: 3
    cpu_utilization:
        target_utilization: 0.6

resources:
    cpu: 1
    memory_gb: 1.5

```

- Replace `MAIL_SERVER` with your SMTP server.
- Replace `MAIL_PORT` with your SMTP port (this must not be a standard SMTP port)
- Replace `MAIL_TLS_ENABLED` with 'true' or 'false'
- Replace `PASSWORD` with your mail server password.
- Replace `USERNAME` with your mail server username.
- Replace `MAIL_SENDER` with the `From` address to be used for emails sent by the app.
- Replace `SECRET` with a random string of about 30 characters. This is used to
  sign user sessions. Changing it and redeploying will force log out all users.
- Replace `MONGODB_URI` with the MongoDB connection URI.
- Replace `GCS_BUCKET` with the name of the Google Cloud Storage bucket that
  will be used to store course catalog snapshots and updates.
- Replace `EMAIL_ERRORS_TO` with a space-separated list of email addresses that
  will be emailed anytime an error occurs (this can be omitted or left blank to
  not send a message for every error).

Important: Keep your app.yaml safe - it's stored outside of git because it
contains your authentication credentials and secret key.

## Build the UI and prepare a deployment directory

```shell
./build.sh ~/schdl-deploy
```

## Enter the prod-like deployment environemtn

WARNING: Commands run this way will impact the production database and Cloud
Storage configured in `app.yaml`.

```shell
cd ~/schdl
. venv/bin/activate
cd ~/schdl-deploy
. prod.env
```

You can now run scripts from the `bin` directory:

- `devServer.py` to run a development server backed by the prod database
  (append `?force_host=prod-host.name` to your URL when opening this in your
  browser to indicate the correct school to use).
- `setAPIKey.py` to update the API key used to publish data updates.
- `generateSnapshot.py` to generate a snapshot file, which can then be uploaded
  to Cloud Storage in place of the latest snapshot in case the snapshot somehow
  gets corrupted.

## Deploy the version in the schdl-deploy directory to App Engine

Before the first time you'll do this, you'll need to first open the App Engine
section of the Google Cloud Console, create a Python Flexible environment app,
and choose a region that the app will run in.

```shell
gcloud app deploy
# When doing first-time deployment or if you've changed cron.yaml:
gcloud app deploy cron.yaml
```
