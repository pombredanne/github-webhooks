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

In a separate shell startup your mongo database (assumes you have mongo
installed already):

        mongodb --dbpath /tmp

Then run the tests:

        python ./webhooks_test.py

Some notes on making changes
--------------------

If you are adding a new type of event to be acted upon, the first step
is to go to your org or repo webhooks and make sure it is being sent.

`https://github.com/organizations/<your-org-or-repo>/settings/hooks/<unique-id-number>`

If your org is set to "Let me select individual events." you will need
to select the new event type, e.g. *Issue comment*.

Once you have the event firing (confirmed at the org or repo webhooks
link above), it is a good idea to copy/paste a json payload from a
fired event to the `test_resources` folder for use in a unit test,
e.g. `forked_repo_issue_comment.json`.

Now that you have confirmed the event is firing, and you have copied the json
payload, it is time to start adding the code that processes the event.

You will need to add a case to the logic in `main.py` that
checks the event type, i.e.:

`elif event == "issue_comment":`

And a "matcher", i.e.:

        <snip>
        elif event == "issue_comment":
            for potential_handler in job_map_config['issue']:
                matcher = potential_handler['match']
                if ( ('branch' not in matcher or re.match(matcher['branch'], branch)) and
                     ('repo' not in matcher or re.match(matcher['repo'], repo)) and
        <snip>

Matchers work like this: if a field does not exist in `map_config.yml` or the
field exists in `map_config.yml` and matches the condition (regex,
string comparison, etc) then the matcher "matches". Matchers iterate
over `map_config.yml` and the *last one* that matches is used to trigger
the jenkins job.

Finally, when adding a new event type, you will likely need a
condition to trigger a jenkins job based on the handler (the result of
the match), i.e.:

                    elif issue_comment:
                        actual_handler = simplejson.loads(simplejson.dumps(handler).replace('{comment}', message).replace('{repo}', repo).replace('{owner}', owner).replace('{issue_number}', str(issue_number)))

NB that the series of chained `.replace` methods replace the
curly-brace-surrounded fields in `map_config.yml` with the values that
have been received from the json payload, e.g.:

                    event_gen = {
                        'type': event,
                        'repo': repo,
                        'repo_owner': owner,
                        'branch': branch,

These replaced fields are typically used as parameters to the jenkins
job that is triggered.

Troubleshooting
---------------

Some common errors you might see when running the tests:

    {   'msg': "'no_message'", 'state': 'error'}

or:

    expected string or buffer
    {   'msg': 'expected string or buffer', 'state': 'error'}

These are often indicative of vars that are unset or that aren't
matching (and thus aren't triggering any jenkins jobs).

Make sure that your json payload is being read correctly to set
required vars - compare how a push event's json payload defines repo
with how it is defined in a pull_request event:

    repo = json['repository']['name']

    repo = json['pull_request']['head']['repo']['name']

If these aren't pulling in valid values from your
`test_resources/new_event_payload.json` you will tend to see errors
like the above.
