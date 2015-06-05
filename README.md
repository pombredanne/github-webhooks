Github Webhooks
===============
Server that handles webhook requests and passes them along to jenkins

Now in docker!

How to run for development
--------------------------

In a separate shell startup your mongo database:

        mongodb --dbpath /tmp

Install dependencies

        virtualenv webhooks_env
        . ./webhooks_env/bin/activate
        pip install -r requirements.txt

Set any environment variables

        export JENKINS_USER=buildmaster

Run Webhooks

        python main.py

You should see the following output and be able to visit the webpage at http://localhost:5001

        $ python main.py
        {'MONGO_DB_NAME': 'dxmanager', 'JENKINS_USER': 'SETME', 'JENKINS_JOB_TOKEN': 'SETME', 'MONGO_DB_PORT': 27017, 'JENKINS_USER_TOKEN': 'SETME', 'JENKINS_URL': 'SETME', 'MONGO_DB_HOST': 'localhost', 'TEST': False, 'DEBUG': True, 'PORT': 5001}
        Loading MONGO_DB_NAME as dxmanager
        Loading JENKINS_USER as SETME
        Loading JENKINS_JOB_TOKEN as SETME
        Loading MONGO_DB_PORT as 27017
        Loading JENKINS_USER_TOKEN as SETME
        Loading JENKINS_URL as SETME
        Loading MONGO_DB_HOST as localhost
        Loading TEST as False
        Loading DEBUG as True
        Loading PORT as 5001
         * Running on http://0.0.0.0:5001/


How to run the tests
--------------------

In a separate shell startup your mongo database:

        mongodb --dbpath /tmp

Then run the tests:

        python ./webhooks_test.py
