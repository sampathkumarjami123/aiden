import json
from concurrent.futures import ThreadPoolExecutor
import unittest
import shutil
from unittest.mock import patch

from fastapi.testclient import TestClient

import aiden_web
from aiden_web import app, engine
from aiden_core import PROFILE_EXPORT_DIR


def _cleanup_profile_exports() -> None:
    if PROFILE_EXPORT_DIR.exists():
        shutil.rmtree(PROFILE_EXPORT_DIR, ignore_errors=True)


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

    def test_api_security_headers_present_on_success(self):
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('x-content-type-options'), 'nosniff')
        self.assertEqual(response.headers.get('x-frame-options'), 'DENY')
        self.assertEqual(response.headers.get('referrer-policy'), 'no-referrer')
        self.assertEqual(response.headers.get('cache-control'), 'no-store')

    def test_api_security_headers_present_on_error(self):
        response = self.client.post('/api/chat', json={'message': 'hello', 'mode': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers.get('x-content-type-options'), 'nosniff')
        self.assertEqual(response.headers.get('x-frame-options'), 'DENY')
        self.assertEqual(response.headers.get('referrer-policy'), 'no-referrer')
        self.assertEqual(response.headers.get('cache-control'), 'no-store')

    def test_stream_api_security_headers_present_on_success(self):
        response = self.client.post('/api/chat/stream', json={'message': 'hello'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('x-content-type-options'), 'nosniff')
        self.assertEqual(response.headers.get('x-frame-options'), 'DENY')
        self.assertEqual(response.headers.get('referrer-policy'), 'no-referrer')
        self.assertEqual(response.headers.get('cache-control'), 'no-store')

    def test_stream_invalid_chat_mode_returns_400(self):
        response = self.client.post('/api/chat/stream', json={'message': 'hello', 'mode': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

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

    def test_stream_request_too_large_returns_413(self):
        with patch('aiden_web.MAX_REQUEST_BYTES', 8):
            response = self.client.post('/api/chat/stream', json={'message': 'this payload is too large'})
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

    def test_stream_rate_limit_returns_429(self):
        with patch('aiden_web.RATE_LIMIT_REQUESTS_PER_WINDOW', 2):
            first = self.client.post('/api/chat/stream', json={'message': 'hello'})
            second = self.client.post('/api/chat/stream', json={'message': 'hello'})
            third = self.client.post('/api/chat/stream', json={'message': 'hello'})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertIn('x-request-id', third.headers)
        self.assertIn('error', third.json())


class StreamChatApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()

    @staticmethod
    def _parse_ndjson(response_text: str):
        lines = [line.strip() for line in response_text.splitlines() if line.strip()]
        return [json.loads(line) for line in lines]

    def test_stream_chat_returns_chunk_and_final_payload(self):
        with patch.object(engine, 'handle_command', return_value=(False, '', {})):
            with patch.object(engine, 'chat_stream', return_value=iter(['Hello', ' there'])):
                response = self.client.post('/api/chat/stream', json={'message': 'Hi'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/x-ndjson', response.headers.get('content-type', ''))

        events = self._parse_ndjson(response.text)
        self.assertGreaterEqual(len(events), 2)
        self.assertEqual(events[0]['type'], 'chunk')
        self.assertEqual(events[0]['text'], 'Hello')
        self.assertEqual(events[1]['type'], 'chunk')
        self.assertEqual(events[1]['text'], ' there')
        self.assertEqual(events[-1]['type'], 'final')
        self.assertEqual(events[-1]['meta']['type'], 'chat')
        self.assertIn('prefs', events[-1])
        self.assertIn('runtime', events[-1])

    def test_stream_chat_handles_command_output(self):
        with patch.object(engine, 'handle_command', return_value=(True, 'Commands:\n  /help', {'type': 'help'})):
            response = self.client.post('/api/chat/stream', json={'message': '/help'})

        self.assertEqual(response.status_code, 200)
        events = self._parse_ndjson(response.text)
        self.assertGreaterEqual(len(events), 2)
        self.assertEqual(events[0]['type'], 'chunk')
        self.assertIn('/help', events[0]['text'])
        self.assertEqual(events[-1]['type'], 'final')
        self.assertEqual(events[-1]['meta']['type'], 'help')

    def test_stream_chat_emits_error_event_when_stream_fails(self):
        with patch.object(engine, 'handle_command', return_value=(False, '', {})):
            with patch.object(engine, 'chat_stream', side_effect=RuntimeError('stream failure')):
                response = self.client.post('/api/chat/stream', json={'message': 'Hi'})

        self.assertEqual(response.status_code, 200)
        events = self._parse_ndjson(response.text)
        self.assertGreaterEqual(len(events), 2)
        self.assertEqual(events[0]['type'], 'error')
        self.assertIn('stream failure', events[0]['error'])
        self.assertEqual(events[-1]['type'], 'final')
        self.assertEqual(events[-1]['meta']['type'], 'error')

    def test_stream_chat_timeout_emits_error_event(self):
        with patch.object(engine, 'handle_command', return_value=(False, '', {})):
            with patch.object(engine, 'chat_stream', return_value=iter(['slow chunk'])):
                with patch('aiden_web.STREAM_MAX_SECONDS', -1):
                    response = self.client.post('/api/chat/stream', json={'message': 'Hi'})

        self.assertEqual(response.status_code, 200)
        events = self._parse_ndjson(response.text)
        self.assertGreaterEqual(len(events), 2)
        self.assertEqual(events[0]['type'], 'error')
        self.assertIn('Streaming response exceeded', events[0]['error'])
        self.assertEqual(events[-1]['type'], 'final')
        self.assertEqual(events[-1]['meta']['type'], 'error')


class InputValidationTests(unittest.TestCase):
    """Verify that Pydantic Field(max_length=...) constraints return 422."""

    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()

    def test_chat_message_too_long_returns_422(self):
        response = self.client.post('/api/chat', json={'message': 'x' * 4001})
        self.assertEqual(response.status_code, 422)

    def test_stream_chat_message_too_long_returns_422(self):
        response = self.client.post('/api/chat/stream', json={'message': 'x' * 4001})
        self.assertEqual(response.status_code, 422)

    def test_task_text_too_long_returns_422(self):
        response = self.client.post('/api/tasks/add', json={'text': 'z' * 501})
        self.assertEqual(response.status_code, 422)

    def test_memory_note_too_long_returns_422(self):
        response = self.client.post('/api/memory/add', json={'note': 'n' * 1001})
        self.assertEqual(response.status_code, 422)

    def test_memory_search_query_too_long_returns_422(self):
        response = self.client.post('/api/memory/search', json={'query': 'q' * 501})
        self.assertEqual(response.status_code, 422)

    def test_profile_name_too_long_returns_422(self):
        response = self.client.post('/api/profiles/create', json={'name': 'p' * 101})
        self.assertEqual(response.status_code, 422)

    def test_task_postpone_zero_days_returns_422(self):
        response = self.client.post('/api/tasks/postpone', json={'task_id': 1, 'days': 0})
        self.assertEqual(response.status_code, 422)

    def test_task_postpone_exceeds_max_days_returns_422(self):
        response = self.client.post('/api/tasks/postpone', json={'task_id': 1, 'days': 366})
        self.assertEqual(response.status_code, 422)


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


class ConcurrencyApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        aiden_web._clear_rate_limit_state()
        self._orig_client = engine.client
        self._orig_dev_mode = engine.dev_mode
        engine.client = None
        engine.dev_mode = True
        engine.reset_chat()
        engine.clear_tasks()

    def tearDown(self):
        engine.client = self._orig_client
        engine.dev_mode = self._orig_dev_mode
        engine.reset_chat()
        engine.clear_tasks()

    @staticmethod
    def _post_chat(message: str):
        with TestClient(app) as client:
            response = client.post('/api/chat', json={'message': message})
            data = response.json()
            return response.status_code, data.get('answer', '')

    @staticmethod
    def _post_task(text: str):
        with TestClient(app) as client:
            response = client.post('/api/tasks/add', json={'text': text})
            data = response.json()
            return response.status_code, data.get('task', {})

    def test_parallel_chat_requests_succeed_and_preserve_history_shape(self):
        total = 8
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda i: self._post_chat(f'parallel chat {i}'), range(total)))

        for status_code, answer in results:
            self.assertEqual(status_code, 200)
            self.assertTrue(answer)

        # system prompt + (user, assistant) per request
        self.assertEqual(len(engine.messages), 1 + (2 * total))

    def test_parallel_task_add_requests_keep_unique_ids(self):
        total = 10
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(lambda i: self._post_task(f'parallel task {i}'), range(total)))

        task_ids = []
        for status_code, task in results:
            self.assertEqual(status_code, 200)
            self.assertIn('id', task)
            task_ids.append(task['id'])

        self.assertEqual(len(task_ids), total)
        self.assertEqual(len(set(task_ids)), total)

        listed = self.client.get('/api/tasks').json()['tasks']
        self.assertEqual(len(listed), total)


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
        _cleanup_profile_exports()
        # Ensure the test profile does not exist before each test
        if self._TEST_PROFILE in engine.list_profiles():
            engine.delete_profile(self._TEST_PROFILE)

    def tearDown(self):
        # Clean up any profile created during the test
        if self._TEST_PROFILE in engine.list_profiles():
            engine.delete_profile(self._TEST_PROFILE)
        _cleanup_profile_exports()

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
