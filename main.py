# Copyright (c) 2015, DataXu
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
This is a Github Web Service Hook script. It uses
Flask to manage URLs. It must be running as an
available Flask service accepting requests.

It needs to be defined on each repository. It will:

1. Parse the branch from the commit.
2. If the branch is named with our naming convention,
   then determine if we have an action for that convention.
3. Call the method to execute that action
4. If the branch does not fall under that category, then
   fall-through to the Git Jenkins plugin notify functionality
   to search for jobs configured for polling that match the
   repository just committed to.
"""

import re
import simplejson
import time
import yaml
import os

from flask import Flask, jsonify
from flask import request

from pymongo import MongoClient
from pymongo import DESCENDING

from jenkins import Jenkins
from jenkins import JenkinsException

stream = open("config.yml", 'r')
app_configs = yaml.load(stream)
print app_configs
for key in app_configs:
    if key in os.environ:
        app_configs[key] = os.environ[key]
    print "Loading {0} as {1}".format(key, app_configs[key])

for config in ['DEBUG', 'TEST']:
    app_configs[config] = str(app_configs[config]).lower() == 'true'

app = Flask(__name__, static_url_path='', static_folder='public/')

# Load default config and override config from an environment variable
app.config.update(app_configs)

client = MongoClient(app.config['MONGO_DB_HOST'], app.config['MONGO_DB_PORT'])
db = client[app.config['MONGO_DB_NAME']]

events_coll = db.events
error_coll = db.errors

jenkins_instance = Jenkins(app.config['JENKINS_URL'],
                           app.config['JENKINS_USER'],
                           app.config['JENKINS_USER_TOKEN'])

running_status = 'running'
job_map_config = {}


@app.route('/reload_config')
def load_map_config():
    _load_map_config()
    return (jsonify(state='done', msg='map_config reloaded', config=job_map_config), 200)


def _load_map_config():
    global job_map_config
    stream = open(app.config['MAP_CONFIG'], 'r')
    job_map_config = yaml.load(stream)

_load_map_config()


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/data')
def data():
    try:
        return (jsonify(
            status=running_status,
            jenkins={'host': app.config['JENKINS_URL'], 'user': app.config['JENKINS_USER']},
            events=list(events_coll.find({}, {'_id': 0}).limit(200).sort('time', DESCENDING)),
            map_config=job_map_config,
            errors=list(error_coll.find({}, {'_id': 0}).limit(200).sort('time', DESCENDING))),
            200)
    except:
        return (jsonify(status='broken'), 200)


@app.route('/test', methods=['GET', 'POST'])
def test():
    data = {}
    # print "TEST"
    # print request.form
    if request.data:
        # data = request.form.to_dict()
        data = simplejson.loads(request.data)
    return (jsonify(state='done', msg='test success', data=data), 200)


@app.route('/search', methods=['GET', 'POST'])
def search():
    return_data = {'results': []}
    state = 'done'
    if request.method == 'POST':
        data = simplejson.loads(request.data)
        search_terms = {}
        for key in data:
            if data[key]:
                search_terms[key] = data[key]
        return_data['results'] = list(events_coll.find(search_terms, {'_id': 0}).limit(100).sort('time', DESCENDING))
    return (jsonify(state=state, **return_data), 200)


@app.route('/trigger', methods=['GET', 'POST'])
def trigger():
    """
    The main entry point; the URL hit is the root of this
    flask application. Determines what action to take via
    functions.
    """
    return_data = {}
    state = 'done'
    msg = "nothing done"

    try:
        if request.method == 'POST':
            event = request.headers.get('X-GitHub-Event')
            if event == 'push' or event == 'pull_request' or event == 'issue_comment':
                json = request.data
                if isinstance(json, basestring):
                    json = simplejson.loads(json)

                    pr_number = None
                    pr_url = None

                    issue_number = None
                    issue_comment = None
                    issue_url = None
                    label = None

                if event == "push":
                    deleted = bool(json['deleted'])
                    created = bool(json['created'])

                    if deleted:
                        message = "deleted"
                    else:
                        message = json['head_commit']['message']

                    owner = json['repository']['owner']['name']
                    repo = json['repository']['name']
                    git_hash = json['after']
                    branch = '_'.join(json['ref'].split('/')[2:])
                    user = json['pusher']['name']

                elif event == "pull_request":
                    deleted = False
                    created = json['action'] in ['opened']

                    owner = json['pull_request']['head']['repo']['owner']['login']
                    repo = json['pull_request']['head']['repo']['name']
                    git_hash = json['pull_request']['head']['sha']
                    branch = json['pull_request']['head']['ref']
                    user = json['pull_request']['user']['login']
                    message = json['action']
                    if 'label' in json:
                        if 'name' in json['label']:
                            label = json['label']['name']
                    pr_number = json['pull_request']['number']
                    pr_url = json['pull_request']['html_url']

                elif event == "issue_comment":
                    deleted = False
                    created = json['action'] in ['created']

                    message = json['comment']['body']
                    user = json['comment']['user']['login']
                    owner = json['repository']['owner']['login']
                    repo = json['repository']['name']
                    git_hash = None
                    branch = None

                    issue_number = json['issue']['number']
                    issue_comment = message
                    issue_url = json['issue']['html_url']

                event_gen = {
                    'type': event,
                    'repo': repo,
                    'repo_owner': owner,
                    'branch': branch,
                    'hash': git_hash,
                    'pusher': user,
                    'action': msg,
                    'message': message,
                    'issue_number': issue_number,
                    'pr_number': pr_number,
                    'pr_url': pr_url,
                    'issue_url': issue_url,
                    'time': int(time.time() * 1000),
                    'job_name': False,
                    'label': label
                }

                events_coll.insert(event_gen)

                if deleted:
                    msg = "delete branch, nothing to do"
                else:
                    handler = False

                    if event == "push":
                        for potential_handler in job_map_config['push']:
                            matcher = potential_handler['match']
                            if ( ('branch' not in matcher or re.match(matcher['branch'], branch)) and
                                 ('repo' not in matcher or re.match(matcher['repo'], repo)) and
                                 ('message' not in matcher or re.search(matcher['message'], message)) and
                                 ('no_message' not in matcher or not re.search(matcher['no_message'], message)) and
                                 ('no_branch' not in matcher or not re.search(matcher['no_branch'], branch)) and
                                 ('owner' not in matcher or re.match(matcher['owner'], owner)) and
                                 ('created' not in matcher or matcher['created'] == created) ):
                                handler = potential_handler

                    elif event == "pull_request":
                        for potential_handler in job_map_config['pr']:
                            matcher = potential_handler['match']
                            if ( ('branch' not in matcher or re.match(matcher['branch'], branch)) and
                                 ('repo' not in matcher or re.match(matcher['repo'], repo)) and
                                 ('message' not in matcher or re.search(matcher['message'], message)) and
                                 ('no_message' not in matcher or not re.search(matcher['no_message'], message)) and
                                 ('label' not in matcher or re.search(matcher['label'], label) and label) and
                                 ('owner' not in matcher or re.match(matcher['owner'], owner)) and
                                 ('created' not in matcher or matcher['created'] == created) and
                                 ('actions' not in matcher or json['action'] in matcher['actions']) ):
                                handler = potential_handler

                    elif event == "issue_comment":
                        for potential_handler in job_map_config['issue']:
                            matcher = potential_handler['match']
                            if ( ('branch' not in matcher or re.match(matcher['branch'], branch)) and
                                 ('repo' not in matcher or re.match(matcher['repo'], repo)) and
                                 ('message' not in matcher or re.search(matcher['message'], message)) and
                                 ('no_message' not in matcher or not re.search(matcher['no_message'], message)) and
                                 ('owner' not in matcher or re.match(matcher['owner'], owner)) and
                                 ('created' not in matcher or matcher['created'] == created) and
                                 ('actions' not in matcher or json['action'] in matcher['actions']) ):
                                handler = potential_handler

                    if not handler:
                        pass
                    else:
                        if pr_number:
                            actual_handler = simplejson.loads(simplejson.dumps(handler).replace('{branch}', branch).replace('{repo}', repo).replace('{owner}', owner).replace('{pr_number}', str(pr_number)))
                        elif issue_comment:
                            actual_handler = simplejson.loads(simplejson.dumps(handler).replace('{comment}', message).replace('{repo}', repo).replace('{owner}', owner).replace('{issue_number}', str(issue_number)))
                        else:
                            actual_handler = simplejson.loads(simplejson.dumps(handler).replace('{branch}', branch).replace('{repo}', repo).replace('{owner}', owner))
                        trigger = actual_handler['trigger']
                        msg = "triggered {0} job".format(trigger['job'])
                        event_gen['job_name'] = trigger['job']

                        if 'create_job' in handler:
                            where_error = 'create_job'
                            msg = "created {0} job from {1}".format(actual_handler['create_job']['job'], actual_handler['create_job']['template'])
                            if not app.config['TEST']:
                                try:
                                    where_error = 'create_job/get_job_config'
                                    job_config = jenkins_instance.get_job_config(actual_handler['create_job']['template'])
                                    if 'replace' in actual_handler['create_job']:
                                        for key in actual_handler['create_job']['replace']:
                                            job_config = job_config.replace(key, actual_handler['create_job']['replace'][key])

                                    where_error = 'create_job/create_job'
                                    new_job = jenkins_instance.create_job(actual_handler['create_job']['job'], job_config)
                                    where_error = 'create_job/enable_job'
                                    jenkins_instance.enable_job(actual_handler['create_job']['job'])

                                except JenkinsException as jenkins_exception:
                                    state = 'error'
                                    error_coll.insert({'time': int(time.time() * 1000), "where": where_error, "msg": "{0}".format(jenkins_exception)})
                                    msg = "Jenkins Error"

                        if not app.config['TEST']:
                            where_error = 'trigger'
                            try:
                                if ('params' in trigger):
                                    where_error = 'trigger/param'
                                    jenkins_instance.build_job(trigger['job'], parameters=trigger['params'], token=app.config['JENKINS_JOB_TOKEN'])
                                else:
                                    where_error = 'trigger/no_param'
                                    jenkins_instance.build_job(trigger['job'], token=app.config['JENKINS_JOB_TOKEN'])

                            except JenkinsException as jenkins_exception:
                                state = 'error'
                                error_coll.insert({'time': int(time.time() * 1000), "where": where_error, "msg": "{0}".format(jenkins_exception)})
                                msg = "Jenkins Error"

                event_gen['action'] = msg
                events_coll.save(event_gen)
                event_gen.pop('_id', None)
                return_data['event'] = event_gen
                if app.config['TEST']:
                    return_data['test_mode'] = True

        return (jsonify(state=state, msg=msg, **return_data), 200)
    except Exception as e:
        print "catch_all error: {0}".format(e)
        error_coll.insert({'time': int(time.time() * 1000), "where": 'catch_all', "msg": "{0}".format(e)})
        return (jsonify(state='error', msg=str(e)), 500)


def clear_db():
    events_coll.remove({})
    error_coll.remove({})
    pass

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=app.config['PORT'])
