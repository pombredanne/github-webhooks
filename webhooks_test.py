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

    def tearDown(self):
        main.clear_db()
        pass

    # helpers
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
        assert data['msg'] == 'triggered business-service-monitor_dev-feature job'
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
        assert data['event']['job_name'] == 'business-service-monitor_dev-feature'

    def test_trigger_rel_new(self):
        data = self.github_trigger('rel_post_bsm_new.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_rel job'
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
        assert data['msg'] == 'triggered business-service-monitor_master job'
        event_data = self.get_data('/data')['events']
        assert len(event_data) == 1
        assert data['event'] == event_data[0]
        assert data['event']['job_name'] == 'business-service-monitor_master'

    # PR
    def test_new_pr(self):
        data = self.github_trigger('new_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered jenkins-jobs_pr job'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'jenkins-jobs'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'ferrants'
        assert data['event']['job_name'] == 'jenkins-jobs_pr'
        assert data['event']['pr_number'] == 134

    def test_new_forked_pr(self):
        data = self.github_trigger('new_forked_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered jenkins-jobs_pr job'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'ferrants'
        assert data['event']['repo'] == 'jenkins-jobs'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'ferrants'
        assert data['event']['job_name'] == 'jenkins-jobs_pr'
        assert data['event']['pr_number'] == 135

    def test_update_forked_pr(self):
        data = self.github_trigger('update_forked_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered jenkins-jobs_pr job'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'ferrants'
        assert data['event']['repo'] == 'jenkins-jobs'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'ferrants'
        assert data['event']['job_name'] == 'jenkins-jobs_pr'
        assert data['event']['pr_number'] == 135

    def test_close_pr(self):
        data = self.github_trigger('close_pr.json', github_event_type='pull_request')
        assert data['state'] == 'done'
        assert data['msg'] == 'nothing done'
        assert data['event']['type'] == 'pull_request'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'jenkins-jobs'
        assert data['event']['branch'] == 'dev-test-pr-hook'
        assert data['event']['pusher'] == 'ferrants'
        assert data['event']['job_name'] is False
        assert data['event']['pr_number'] == 134

    # Issue comments
    def test_add_issue_comment(self):
        data = self.github_trigger('add_issue_comment.json', github_event_type='issue_comment')
        assert data['state'] == 'done'
        assert data['event']['message'] == 'add_label: not_ready'
        assert data['event']['type'] == 'issue_comment'
        assert data['event']['pusher'] == 'dx-pbuckley'
        assert data['event']['repo'] == 'dxng'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['issue_number'] == 60

    def test_forked_issue_comment(self):
        data = self.github_trigger('forked_issue_comment.json', github_event_type='issue_comment')
        assert data['state'] == 'done'
        assert data['event']['message'] == 'add_labels: stale, jira'
        assert data['event']['type'] == 'issue_comment'
        assert data['event']['pusher'] == 'dx-pbuckley'
        assert data['event']['repo'] == 'dxng'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['issue_number'] == 390

    # Regression
    def test_delete_push(self):
        data = self.github_trigger('delete_push.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'delete branch, nothing to do'
        assert data['event']['type'] == 'push'
        assert data['event']['repo_owner'] == 'dataxu'
        assert data['event']['repo'] == 'jenkins-jobs'
        assert data['event']['branch'] == 'dev-remove-bsm-timer'
        assert data['event']['pusher'] == 'ferrants'
        assert data['event']['job_name'] is False

    # Search
    def test_search_get(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.get_data('/search')
        assert search_data['state'] == 'done'
        assert len(search_data['results']) == 0

    def test_search_repo(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.post_data('/search', {'repo': 'business-service-monitor'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['repo'] == 'business-service-monitor'

    def test_search_branch(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.post_data('/search', {'branch': 'master'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['branch'] == 'master'

    def test_search_pusher(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.post_data('/search', {'pusher': 'kaneda'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['pusher'] == 'kaneda'

    def test_search_hash(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.post_data('/search', {'hash': 'd4e5330448fd8e0a42f44df2187318149b738672'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

    def test_search_multi(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.post_data('/search', {'branch': 'master', 'hash': 'd4e5330448fd8e0a42f44df2187318149b738672'})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

    def test_search_empty(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.post_data('/search', {})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

    def test_search_blank(self):
        data = self.github_trigger('master_post_bsm.json')
        assert data['state'] == 'done'
        assert data['msg'] == 'triggered business-service-monitor_master job'
        search_data = self.post_data('/search', {'hash': ''})
        assert len(search_data['results']) == 1
        assert search_data['results'][0]['hash'] == 'd4e5330448fd8e0a42f44df2187318149b738672'

if __name__ == '__main__':
    unittest.main()
