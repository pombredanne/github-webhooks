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

import os
import main
import unittest
import simplejson


class WebhooksTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        main.app.config['TEST'] = True  # dont trigger jobs
        main.app.config['MONGO_DB_NAME'] = 'webhooks-test'
        self.app = main.app.test_client()
        main.clear_db()

    def setUp(self):
        self.set_map_config('dx_map_config.yml')

    def tearDown(self):
        main.clear_db()
        pass

    # helpers
    def set_map_config(self, map_config):
        main.app.config['MAP_CONFIG'] = 'map_configs/%s' % map_config
        self.get_data('/reload_config')

    def get_data(self, page, headers={'Content-Type': 'application/json'}):
        result = self.app.get(page, follow_redirects=True, headers=headers)
        return simplejson.loads(result.data)

    def post_data(self, page, data, headers={'Content-Type': 'application/json'}):
        result = self.app.post(page, data=simplejson.dumps(data), follow_redirects=True, headers=headers)
        return simplejson.loads(result.data)

    def load_json_resource(self, filename):
        with open(os.path.join(os.path.dirname(__file__), 'test_resources', filename)) as data_file:
            data = simplejson.load(data_file)
        return data

    def github_trigger(self, filename, github_event_type='push'):
        post_data = self.load_json_resource(filename)
        return self.post_data('/trigger', post_data, headers={'X-GitHub-Event': github_event_type, 'Content-Type': 'application/json'})

    # testcases
    def test_testpage_get(self):
        data = self.get_data('/test')
        assert data['state'] == 'done'
        assert data['msg'] == 'test success'
        assert data['data'] == {}

    def test_testpage_post(self):
        data = self.post_data('/test', {'nice': 'yeah', 'second': 'value'})
        assert data['state'] == 'done'
        assert data['msg'] == 'test success'
        assert data['data'] == {'second': 'value', 'nice': 'yeah'}
        assert data['data'] == {'nice': 'yeah', 'second': 'value'}

    def test_datapage(self):
        data = self.get_data('/data')
        assert data['status'] == 'running'
        assert data['events'] == []

    def test_trigger_get(self):
        data = self.get_data('/trigger')
        assert data == {'msg': 'nothing done', 'state': 'done'}

    def test_trigger_dev(self):
        data = self.github_trigger('dev_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_dev-feature job'
        event_data = self.get_data('/data')['events']
        assert len(event_data) == 1
        assert data['event'] == event_data[0]
        assert 'type' in data['event']
        assert 'repo' in data['event']
        assert 'branch' in data['event']
        assert 'hash' in data['event']
        assert 'time' in data['event']
        assert 'pusher' in data['event']
        assert 'job_name' in data['event']
        assert 'action' in data['event']
        assert data['event']['job_name'] == 'github-webhooks_dev-feature'

    def test_trigger_rel_new(self):
        data = self.github_trigger('rel_post_bsm_new.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_rel job'
        event_data = self.get_data('/data')['events']
        assert len(event_data) == 1
        assert data['event'] == event_data[0]
        assert data['event']['job_name'] is not False

    def test_trigger_rel_notnew(self):
        data = self.github_trigger('rel_post_bsm_notnew.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'nothing done'
        event_data = self.get_data('/data')['events']
        assert len(event_data) == 1
        assert data['event'] == event_data[0]
        assert data['event']['job_name'] is False

    def test_trigger_master(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        event_data = self.get_data('/data')['events']
        assert len(event_data) == 1
        assert data['event'] == event_data[0]
        assert data['event']['job_name'] == 'github-webhooks_master'

    # PR
    def test_new_pr(self):
        data = self.github_trigger('new_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-pr_pr job'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['job_name'] == 'github-pr_pr'
        assert data['event']['pr_number'] == 134

    def test_new_forked_pr(self):
        data = self.github_trigger('new_forked_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-pr_pr job'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'dxbuildmaster'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['job_name'] == 'github-pr_pr'
        assert data['event']['pr_number'] == 135

    def test_update_forked_pr(self):
        data = self.github_trigger('update_forked_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-pr_pr job'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'dxbuildmaster'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['job_name'] == 'github-pr_pr'
        assert data['event']['pr_number'] == 135

    def test_close_pr(self):
        data = self.github_trigger('close_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'nothing done'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['job_name'] is False
        assert data['event']['pr_number'] == 134

    def test_label_pr(self):
        data = self.github_trigger('label_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered tools_create-int-branch job'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'cms'
        assert data['event']['branch'] == 'fakersbranch'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['job_name'] == 'tools_create-int-branch'
        assert data['event']['pr_number'] == 25

    # Issue comments
    def test_add_issue_comment(self):
        data = self.github_trigger('add_issue_comment.json', github_event_type='issue_comment')
        assert data['state'] == 'done'
        assert data['event']['message'] == 'add_label: not_ready'
        assert data['event']['type'] == 'issue_comment'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['issue_number'] == 60
        assert data['event']['issue_url'] == 'https://github.com/dataxu/github-pr/issues/60'

    def test_forked_issue_comment(self):
        data = self.github_trigger('forked_issue_comment.json', github_event_type='issue_comment')
        assert data['state'] == 'done'
        assert data['event']['message'] == 'add_labels: stale, jira'
        assert data['event']['type'] == 'issue_comment'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['issue_number'] == 390
        assert data['event']['issue_url'] == 'https://github.com/dataxu/github-pr/pull/390'

    def test_shipit_comment_automerge(self):
        data = self.github_trigger('ship_it_comment.json', github_event_type='issue_comment')
        assert data['state'] == 'done'
        assert data['event']['message'] == ':shipit:'
        assert data['event']['type'] == 'issue_comment'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['issue_number'] == 390
        assert data['event']['issue_url'] == 'https://github.com/dataxu/github-pr/pull/390'

    # Pushes

    def test_dev_apu_push(self):
        data = self.github_trigger('dev-apu-push.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'nothing done'
        assert data['event']['type'] == 'push'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['branch'] == 'dev-auto_pom_update'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['job_name'] is False

    # Regression
    def test_delete_push(self):
        data = self.github_trigger('delete_push.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'delete branch, nothing to do'
        assert data['event']['type'] == 'push'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'github-pr'
        assert data['event']['branch'] == 'dev-remove-bsm-timer'
        assert data['event']['pusher'] == 'dxbuildmaster'
        assert data['event']['job_name'] is False

    # Search
    def test_search_get(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.get_data('/search')
        assert search_data['state'] == 'done'
        assert len(search_data['results']) == 0

    def test_search_repo(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.post_data('/search', {'repo': 'github-webhooks'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['repo'] == 'github-webhooks'

    def test_search_branch(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.post_data('/search', {'branch': 'master'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['branch'] == 'master'

    def test_search_pusher(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.post_data('/search', {'pusher': 'dxbuildmaster'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['pusher'] == 'dxbuildmaster'

    def test_search_hash(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.post_data('/search', {'hash': 'd4e5330448fd8e0a42f44df2187318149b738672'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

    def test_search_multi(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.post_data('/search', {'branch': 'master', 'hash': 'd4e5330448fd8e0a42f44df2187318149b738672'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

    def test_search_empty(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.post_data('/search', {})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

    def test_search_blank(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered github-webhooks_master job'
        search_data = self.post_data('/search', {'hash': ''})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

if __name__ == '__main__':
    unittest.main()
