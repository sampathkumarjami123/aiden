import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import aiden_web
from aiden_web import app, engine


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get('ok'), True)
        self.assertEqual(payload.get('service'), 'aiden-web')

    def test_state_endpoint_shape(self):
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        self.assertIn('x-request-id', response.headers)
        payload = response.json()
        for key in ('prefs', 'profiles', 'tasks', 'memory_notes', 'runtime'):
            self.assertIn(key, payload)

    def test_invalid_profile_switch_returns_400(self):
        response = self.client.post('/api/profiles/switch', json={'name': 'does-not-exist'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('x-request-id', response.headers)
        self.assertIn('error', response.json())

    def test_invalid_task_done_returns_400(self):
        response = self.client.post('/api/tasks/done', json={'task_id': 99999})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_invalid_chat_mode_returns_400(self):
        response = self.client.post('/api/chat', json={'message': 'hello', 'mode': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_request_too_large_returns_413(self):
        with patch('aiden_web.MAX_REQUEST_BYTES', 8):
            response = self.client.post('/api/chat', json={'message': 'this payload is too large'})
        self.assertEqual(response.status_code, 413)
        self.assertIn('x-request-id', response.headers)
        self.assertIn('error', response.json())

    def test_rate_limit_returns_429(self):
        with patch('aiden_web.RATE_LIMIT_REQUESTS_PER_WINDOW', 2):
            first = self.client.get('/api/state')
            second = self.client.get('/api/state')
            third = self.client.get('/api/state')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertIn('x-request-id', third.headers)
        self.assertIn('error', third.json())


class TaskApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()
        engine.clear_tasks()

    def test_task_list_returns_empty_after_clear(self):
        response = self.client.get('/api/tasks')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['tasks'], [])

    def test_task_add_returns_task_shape(self):
        response = self.client.post('/api/tasks/add', json={'text': 'Write tests'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        task = payload['task']
        for key in ('id', 'text', 'done', 'priority', 'due_date', 'created_at'):
            self.assertIn(key, task)
        self.assertEqual(task['text'], 'Write tests')
        self.assertFalse(task['done'])
        self.assertEqual(task['priority'], 'medium')

    def test_task_add_with_priority_and_due_date(self):
        response = self.client.post(
            '/api/tasks/add',
            json={'text': 'Deploy release', 'priority': 'high', 'due_date': '2026-06-01'},
        )
        self.assertEqual(response.status_code, 200)
        task = response.json()['task']
        self.assertEqual(task['priority'], 'high')
        self.assertEqual(task['due_date'], '2026-06-01')

    def test_task_add_empty_text_returns_400(self):
        response = self.client.post('/api/tasks/add', json={'text': '   '})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_task_add_invalid_priority_returns_400(self):
        response = self.client.post('/api/tasks/add', json={'text': 'Task', 'priority': 'urgent'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_task_add_invalid_due_date_returns_400(self):
        response = self.client.post('/api/tasks/add', json={'text': 'Task', 'due_date': 'not-a-date'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_task_done_marks_task_complete(self):
        task_id = self.client.post('/api/tasks/add', json={'text': 'Finish report'}).json()['task']['id']
        response = self.client.post('/api/tasks/done', json={'task_id': task_id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['task']['done'])

    def test_task_done_invalid_id_returns_400(self):
        response = self.client.post('/api/tasks/done', json={'task_id': 99999})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_task_edit_updates_text(self):
        task_id = self.client.post('/api/tasks/add', json={'text': 'Old text'}).json()['task']['id']
        response = self.client.post('/api/tasks/edit', json={'task_id': task_id, 'text': 'New text'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['task']['text'], 'New text')

    def test_task_edit_invalid_id_returns_400(self):
        response = self.client.post('/api/tasks/edit', json={'task_id': 99999, 'text': 'Updated'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_task_postpone_advances_due_date(self):
        self.client.post('/api/tasks/add', json={'text': 'Pending task', 'due_date': '2026-01-10'})
        task_id = self.client.get('/api/tasks').json()['tasks'][0]['id']
        response = self.client.post('/api/tasks/postpone', json={'task_id': task_id, 'days': 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['task']['due_date'], '2026-01-15')

    def test_task_postpone_invalid_id_returns_400(self):
        response = self.client.post('/api/tasks/postpone', json={'task_id': 99999, 'days': 1})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_task_remove_deletes_task(self):
        task_id = self.client.post('/api/tasks/add', json={'text': 'To remove'}).json()['task']['id']
        response = self.client.post('/api/tasks/remove', json={'task_id': task_id})
        self.assertEqual(response.status_code, 200)
        ids = [t['id'] for t in response.json()['tasks']]
        self.assertNotIn(task_id, ids)

    def test_task_remove_invalid_id_returns_400(self):
        response = self.client.post('/api/tasks/remove', json={'task_id': 99999})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_task_clear_empties_list(self):
        self.client.post('/api/tasks/add', json={'text': 'Task A'})
        self.client.post('/api/tasks/add', json={'text': 'Task B'})
        response = self.client.post('/api/tasks/clear')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['tasks'], [])


class MemoryApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()
        engine.clear_memory_notes()

    def test_memory_list_returns_empty_after_clear(self):
        response = self.client.get('/api/memory')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['memory_notes'], [])

    def test_memory_add_returns_note(self):
        response = self.client.post('/api/memory/add', json={'note': 'Prefer dark mode'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['note'], 'Prefer dark mode')
        self.assertIn('Prefer dark mode', payload['memory_notes'])

    def test_memory_add_empty_note_returns_400(self):
        response = self.client.post('/api/memory/add', json={'note': '   '})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_memory_add_appears_in_list(self):
        self.client.post('/api/memory/add', json={'note': 'Reminder: standup at 9am'})
        response = self.client.get('/api/memory')
        self.assertIn('Reminder: standup at 9am', response.json()['memory_notes'])

    def test_memory_clear_empties_notes(self):
        self.client.post('/api/memory/add', json={'note': 'Note one'})
        self.client.post('/api/memory/add', json={'note': 'Note two'})
        response = self.client.post('/api/memory/clear')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['memory_notes'], [])

    def test_memory_search_returns_matching_notes(self):
        self.client.post('/api/memory/add', json={'note': 'User loves Python programming'})
        self.client.post('/api/memory/add', json={'note': 'User dislikes early mornings'})
        response = self.client.post('/api/memory/search', json={'query': 'Python'})
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertTrue(any('Python' in r for r in results))

    def test_memory_search_no_match_returns_empty(self):
        self.client.post('/api/memory/add', json={'note': 'Unrelated note about coffee'})
        response = self.client.post('/api/memory/search', json={'query': 'quantum physics'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [])


class ProfileApiTests(unittest.TestCase):
    _TEST_PROFILE = 'test-api-profile'

    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()
        # Ensure the test profile does not exist before each test
        if self._TEST_PROFILE in engine.list_profiles():
            engine.delete_profile(self._TEST_PROFILE)

    def tearDown(self):
        # Clean up any profile created during the test
        if self._TEST_PROFILE in engine.list_profiles():
            engine.delete_profile(self._TEST_PROFILE)

    def test_state_includes_profiles_list(self):
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        profiles = response.json()['profiles']
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)

    def test_profile_create_adds_to_list(self):
        response = self.client.post('/api/profiles/create', json={'name': self._TEST_PROFILE})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertIn(self._TEST_PROFILE, payload['profiles'])

    def test_profile_create_duplicate_returns_400(self):
        self.client.post('/api/profiles/create', json={'name': self._TEST_PROFILE})
        response = self.client.post('/api/profiles/create', json={'name': self._TEST_PROFILE})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_profile_create_empty_name_returns_400(self):
        response = self.client.post('/api/profiles/create', json={'name': '   '})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_profile_switch_succeeds(self):
        self.client.post('/api/profiles/create', json={'name': self._TEST_PROFILE})
        response = self.client.post('/api/profiles/switch', json={'name': self._TEST_PROFILE})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertIn(self._TEST_PROFILE, payload['profiles'])

    def test_profile_delete_removes_from_list(self):
        self.client.post('/api/profiles/create', json={'name': self._TEST_PROFILE})
        response = self.client.post('/api/profiles/delete', json={'name': self._TEST_PROFILE})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertNotIn(self._TEST_PROFILE, response.json()['profiles'])

    def test_profile_delete_unknown_returns_400(self):
        response = self.client.post('/api/profiles/delete', json={'name': 'no-such-profile'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_profile_export_returns_payload(self):
        response = self.client.post('/api/profiles/export')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertIn('payload', payload)
        self.assertIn('profile_name', payload['payload'])

    def test_profile_import_creates_and_activates(self):
        self.client.post('/api/profiles/create', json={'name': self._TEST_PROFILE})
        export_payload = self.client.post('/api/profiles/export').json()['payload']
        # Delete and re-import under the same name
        engine.delete_profile(self._TEST_PROFILE)
        response = self.client.post(
            '/api/profiles/import',
            json={'profile_name': self._TEST_PROFILE, 'profile_data': export_payload.get('profile', {})},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertIn(self._TEST_PROFILE, response.json()['profiles'])


if __name__ == '__main__':
    unittest.main()
