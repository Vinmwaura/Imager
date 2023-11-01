# Imager

Simple Image Sharing website written with Flask.

## Requirements
+ Python 3

## Setup
1. Install Postgres and it's dependecies (libpq-dev).
2. Create production database:
```
sudo su - postgres
psql
CREATE DATABASE <dbname>;
CREATE USER <user> WITH ENCRYPTED PASSWORD <pwd>;
GRANT ALL PRIVILEGES ON DATABASE <dbname> TO <user>;
```
3. Create testing database:
```
CREATE DATABASE <testing_dbname>;
CREATE USER <testing_user> WITH ENCRYPTED PASSWORD <testing_pwd>;
GRANT ALL PRIVILEGES ON DATABASE <testing_dbname> TO <testing_user>;
```
5. Install virtualenvwrapper.
6. Create virtualenv:
```
mkvirtualenv imager_env
```
3. Activate virtual env:
```
workon imager_env
```
4. Install Python libraries:
```
pip install -r requirements.txt
```
6. Create a .env file in the root of the project and add the following variables:
```
SECRET_KEY=<Generate Secret Key and add here, not to be shared>
FLASK_ENV=production
FLASK_DEBUG=False
SQLALCHEMY_DATABASE_URI=postgresql://<user>:<pwd>@<postgres_server_ip>:<port>/<dbname>
TEST_SQLALCHEMY_DATABASE_URI=postgresql://<testing_user>:<testing_pwd>@<postgres_server_ip>:<port>/<testing_dbname>
MAIL_SERVER="smtp.gmail.com"
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=<sender-email>
MAIL_PASSWORD=<email-password>
MAIL_DEBUG=1
TEST_EMAIL_CONFIG="<test-sender-email>
AUTHLIB_INSECURE_TRANSPORT=1
TESTING=False
```
7. Generate database tables:
```
flask db upgrade
```
8. Create a super user (won't require sending an email to activate account)
```
flask auth createsuperuser
```

## Running
To run the webapp, run the following:
```
sudo chmod +x run.sh
sh run.sh
```

## Screenshot Examples
### Front page (No image uploaded)
![Front_page_no_picture](./assets/42a1fbd2-0c97-4337-ab0e-c18fdfe2c83d.png)

### Front page (Image uploaded)
![Front_page_with_picture](./assets/d4509c21-66f2-49e6-a7b6-167a305d3cf8.png)

### Upload picture page
![Upload_picture](./assets/e975f7af-ae11-4dbe-a0d5-7133396f3c15.png)

### Admin page
![Admin_page](./assets/c32653ac-e3cd-437d-896f-b18c16a24c14.png)


