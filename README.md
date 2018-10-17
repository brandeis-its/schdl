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
   FLASK_MAIL_PASSWORD: 'PASSWORD' 
   FLASK_MAIL_USERNAME: 'USERNAME' 
   FLASK_SECRET_KEY: 'SECRET' 
   SCHDL_DB_URI: 'MONGODB_URI'

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

- Replace `PASSWORD` with your mail server password.
- Replace `USERNAME` with your mail server username.
- Replace `FLASK_SECRET_KEY` with a random string of about 30 characters. This is used to sign user sessions. Changing it and redeploying will force log out all users.
- Replace `MONGODB_URI` with the MongoDB connection URI.

Important: Keep your app.yaml safe - it's stored outside of git because it contains your authentication credentials and secret key.

## Build the UI and prepare a deployment directory

```shell
mkdir -p ~/schdl-deploy
./build.sh ~/schdl-deploy
```

# Deploy the version in the schdl-deploy directory to App Engine

Before the first time you'll do this, you'll need to first open the App Engine section of the Google Cloud Console, create a Python Flexible environment app, and choose a region that the app will run in.

```shell
gcloud app deploy
```
