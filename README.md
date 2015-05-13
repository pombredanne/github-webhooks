Github Webhooks
===============
Server that handles webhook requests and passes them along to jenkins

Now in docker!

How to run the tests
--------------------

In a separate shell startup your mongo database:

        mongodb --dbpath /tmp

Then run the tests:

        python ./webhooks_test.py
