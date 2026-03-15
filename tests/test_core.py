import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiden_core import AidenEngine, ROOT, _resolve_data_root


def _make_engine(tmp_dir: Path) -> AidenEngine:
    """Create a sandboxed AidenEngine that writes to a temp directory."""
    env = {
        "OPENAI_API_KEY": "",
        "AIDEN_DEV_MODE": "true",
        "AIDEN_DATA_DIR": str(tmp_dir),
    }
    with patch.dict(os.environ, env, clear=False):
        return AidenEngine()


class CoreSanityTests(unittest.TestCase):
    def test_resolve_data_root_defaults_to_project_root(self):
        self.assertEqual(_resolve_data_root(None), ROOT)

    def test_resolve_data_root_resolves_relative_path(self):
        self.assertEqual(_resolve_data_root('runtime_data'), ROOT / 'runtime_data')

    def test_resolve_data_root_keeps_absolute_path(self):
        absolute = (ROOT / 'absolute_data').resolve()
        self.assertEqual(_resolve_data_root(str(absolute)), absolute)

    def test_parse_max_messages_defaults_for_invalid_value(self):
        self.assertEqual(AidenEngine._parse_max_messages('abc'), 30)

    def test_parse_max_messages_enforces_minimum(self):
        self.assertEqual(AidenEngine._parse_max_messages('1'), 5)

    def test_parse_max_messages_accepts_valid_int(self):
        self.assertEqual(AidenEngine._parse_max_messages('40'), 40)

    def test_sanitize_profile_normalizes_invalid_fields(self):
        payload = {
            'name': '   ',
            'mode': 'unknown-mode',
            'short_responses': 'maybe',
            'tasks': 'bad',
            'memory_notes': {'bad': 'value'},
        }
        result = AidenEngine._sanitize_profile(payload)
        self.assertEqual(result['name'], 'User')
        self.assertEqual(result['mode'], 'study')
        self.assertEqual(result['short_responses'], 'false')
        self.assertEqual(result['tasks'], [])
        self.assertEqual(result['memory_notes'], [])


class TaskEngineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_task_returns_task_with_expected_fields(self):
        task = self.engine.add_task('Buy milk')
        for key in ('id', 'text', 'done', 'priority', 'due_date', 'created_at'):
            self.assertIn(key, task)
        self.assertEqual(task['text'], 'Buy milk')
        self.assertFalse(task['done'])
        self.assertEqual(task['priority'], 'medium')

    def test_add_task_ids_are_unique_and_incrementing(self):
        t1 = self.engine.add_task('First')
        t2 = self.engine.add_task('Second')
        self.assertGreater(t2['id'], t1['id'])

    def test_add_task_invalid_priority_raises(self):
        with self.assertRaises(ValueError):
            self.engine.add_task('Task', priority='urgent')

    def test_add_task_invalid_due_date_raises(self):
        with self.assertRaises(ValueError):
            self.engine.add_task('Task', due_date='not-a-date')

    def test_add_task_empty_text_raises(self):
        with self.assertRaises(ValueError):
            self.engine.add_task('   ')

    def test_add_task_with_due_date_and_priority(self):
        task = self.engine.add_task('Deploy', due_date='2026-12-01', priority='high')
        self.assertEqual(task['due_date'], '2026-12-01')
        self.assertEqual(task['priority'], 'high')

    def test_list_tasks_sorts_undone_before_done(self):
        t1 = self.engine.add_task('A')
        t2 = self.engine.add_task('B')
        self.engine.complete_task(t1['id'])
        tasks = self.engine.list_tasks()
        self.assertFalse(tasks[0]['done'])
        self.assertTrue(tasks[-1]['done'])

    def test_complete_task_marks_done(self):
        task = self.engine.add_task('Write report')
        done = self.engine.complete_task(task['id'])
        self.assertTrue(done['done'])

    def test_complete_task_invalid_id_raises(self):
        with self.assertRaises(ValueError):
            self.engine.complete_task(99999)

    def test_edit_task_updates_text(self):
        task = self.engine.add_task('Old text')
        updated = self.engine.edit_task(task['id'], text='New text')
        self.assertEqual(updated['text'], 'New text')

    def test_edit_task_updates_priority(self):
        task = self.engine.add_task('Task')
        updated = self.engine.edit_task(task['id'], priority='low')
        self.assertEqual(updated['priority'], 'low')

    def test_edit_task_updates_due_date(self):
        task = self.engine.add_task('Task')
        updated = self.engine.edit_task(task['id'], due_date='2027-01-01')
        self.assertEqual(updated['due_date'], '2027-01-01')

    def test_edit_task_empty_text_raises(self):
        task = self.engine.add_task('Task')
        with self.assertRaises(ValueError):
            self.engine.edit_task(task['id'], text='  ')

    def test_edit_task_invalid_id_raises(self):
        with self.assertRaises(ValueError):
            self.engine.edit_task(99999, text='Updated')

    def test_postpone_task_advances_existing_due_date(self):
        task = self.engine.add_task('Task', due_date='2026-01-10')
        updated = self.engine.postpone_task(task['id'], days=5)
        self.assertEqual(updated['due_date'], '2026-01-15')

    def test_postpone_task_no_due_uses_today_plus_days(self):
        from datetime import datetime, timedelta
        task = self.engine.add_task('Task')
        updated = self.engine.postpone_task(task['id'], days=3)
        expected = (datetime.now().date() + timedelta(days=3)).isoformat()
        self.assertEqual(updated['due_date'], expected)

    def test_postpone_task_invalid_id_raises(self):
        with self.assertRaises(ValueError):
            self.engine.postpone_task(99999)

    def test_postpone_task_zero_days_raises(self):
        task = self.engine.add_task('Task')
        with self.assertRaises(ValueError):
            self.engine.postpone_task(task['id'], days=0)

    def test_remove_task_deletes_task(self):
        task = self.engine.add_task('Remove me')
        self.engine.remove_task(task['id'])
        ids = [t['id'] for t in self.engine.list_tasks()]
        self.assertNotIn(task['id'], ids)

    def test_remove_task_invalid_id_raises(self):
        with self.assertRaises(ValueError):
            self.engine.remove_task(99999)

    def test_clear_tasks_empties_list(self):
        self.engine.add_task('A')
        self.engine.add_task('B')
        self.engine.clear_tasks()
        self.assertEqual(self.engine.list_tasks(), [])


class MemoryEngineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_memory_note_stores_and_returns_note(self):
        saved = self.engine.add_memory_note('Prefers visual examples')
        self.assertEqual(saved, 'Prefers visual examples')
        self.assertIn('Prefers visual examples', self.engine.list_memory_notes())

    def test_add_memory_note_empty_raises(self):
        with self.assertRaises(ValueError):
            self.engine.add_memory_note('   ')

    def test_list_memory_notes_returns_all(self):
        self.engine.add_memory_note('Note A')
        self.engine.add_memory_note('Note B')
        notes = self.engine.list_memory_notes()
        self.assertIn('Note A', notes)
        self.assertIn('Note B', notes)

    def test_clear_memory_notes_empties_list(self):
        self.engine.add_memory_note('Note A')
        self.engine.clear_memory_notes()
        self.assertEqual(self.engine.list_memory_notes(), [])

    def test_memory_notes_capped_at_100(self):
        for i in range(105):
            self.engine.preferences.setdefault('memory_notes', []).append(f'Note {i}')
        self.engine.add_memory_note('Overflow')
        self.assertLessEqual(len(self.engine.list_memory_notes()), 100)

    def test_recall_memory_notes_returns_matching_notes(self):
        self.engine.add_memory_note('Prefers visual learning')
        self.engine.add_memory_note('Likes debugging challenges')
        results = self.engine.recall_memory_notes('visual learning')
        self.assertTrue(any('visual' in r for r in results))

    def test_recall_memory_notes_no_match_returns_empty(self):
        self.engine.add_memory_note('Completely unrelated note')
        results = self.engine.recall_memory_notes('quantum mechanics xyz')
        self.assertEqual(results, [])

    def test_recall_memory_notes_respects_limit(self):
        for i in range(10):
            self.engine.add_memory_note(f'Topic {i} study learning')
        results = self.engine.recall_memory_notes('study learning', limit=3)
        self.assertLessEqual(len(results), 3)


class ProfileEngineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_list_profiles_contains_default(self):
        self.assertIn('default', self.engine.list_profiles())

    def test_create_profile_adds_to_list(self):
        self.engine.create_profile('exam-prep')
        self.assertIn('exam-prep', self.engine.list_profiles())

    def test_create_profile_normalizes_name(self):
        created = self.engine.create_profile('My Profile')
        self.assertEqual(created, 'my-profile')
        self.assertIn('my-profile', self.engine.list_profiles())

    def test_create_profile_duplicate_raises(self):
        self.engine.create_profile('dup')
        with self.assertRaises(ValueError):
            self.engine.create_profile('dup')

    def test_create_profile_empty_name_raises(self):
        with self.assertRaises(ValueError):
            self.engine.create_profile('  ')

    def test_switch_profile_changes_active(self):
        self.engine.create_profile('alt')
        self.engine.switch_profile('alt')
        self.assertEqual(self.engine.active_profile, 'alt')

    def test_switch_profile_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.engine.switch_profile('does-not-exist')

    def test_delete_profile_removes_from_list(self):
        self.engine.create_profile('to-delete')
        self.engine.delete_profile('to-delete')
        self.assertNotIn('to-delete', self.engine.list_profiles())

    def test_delete_profile_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.engine.delete_profile('ghost')

    def test_delete_only_profile_raises(self):
        with self.assertRaises(ValueError):
            self.engine.delete_profile('default')

    def test_delete_active_profile_switches_to_another(self):
        self.engine.create_profile('fallback')
        self.engine.switch_profile('default')
        self.engine.delete_profile('default')
        self.assertNotEqual(self.engine.active_profile, 'default')

    def test_export_active_profile_creates_file(self):
        path = self.engine.export_active_profile()
        self.assertTrue(path.exists())
        payload = json.loads(path.read_text())
        self.assertIn('profile_name', payload)
        self.assertIn('profile', payload)

    def test_import_profile_activates_new_profile(self):
        profile_data = {'name': 'Tester', 'mode': 'coding'}
        imported = self.engine.import_profile_from_json('imported', profile_data)
        self.assertEqual(imported, 'imported')
        self.assertEqual(self.engine.active_profile, 'imported')


class PreferencesEngineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_set_mode_valid(self):
        for mode in ('study', 'coding', 'idea', 'productivity'):
            result = self.engine.set_mode(mode)
            self.assertIn(mode, result.lower())
            self.assertEqual(self.engine.preferences['mode'], mode)

    def test_set_mode_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.engine.set_mode('unknown')

    def test_set_name_strips_whitespace(self):
        result = self.engine.set_name('  Alice  ')
        self.assertEqual(result, 'Alice')
        self.assertEqual(self.engine.preferences['name'], 'Alice')

    def test_set_name_empty_raises(self):
        with self.assertRaises(ValueError):
            self.engine.set_name('  ')

    def test_set_short_responses(self):
        self.engine.set_short_responses(True)
        self.assertEqual(self.engine.preferences['short_responses'], 'true')
        self.engine.set_short_responses(False)
        self.assertEqual(self.engine.preferences['short_responses'], 'false')

    def test_set_learning_style_updates_preference(self):
        self.engine.set_learning_style('visual diagrams')
        self.assertEqual(self.engine.preferences['learning_style'], 'visual diagrams')

    def test_set_learning_style_empty_raises(self):
        with self.assertRaises(ValueError):
            self.engine.set_learning_style('  ')

    def test_set_focus_goal_updates_and_clears(self):
        self.engine.set_focus_goal('Pass the exam')
        self.assertEqual(self.engine.preferences['focus_goal'], 'Pass the exam')
        self.engine.set_focus_goal('')
        self.assertEqual(self.engine.preferences['focus_goal'], '')

    def test_set_interests_updates_preference(self):
        self.engine.set_interests('AI, robotics')
        self.assertEqual(self.engine.preferences['interests'], 'AI, robotics')

    def test_get_preferences_includes_active_profile(self):
        prefs = self.engine.get_preferences()
        self.assertIn('active_profile', prefs)


class CommandHandlerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_non_command_returns_not_handled(self):
        handled, _, _ = self.engine.handle_command('Hello there')
        self.assertFalse(handled)

    def test_help_command(self):
        handled, output, meta = self.engine.handle_command('/help')
        self.assertTrue(handled)
        self.assertIn('/mode', output)
        self.assertEqual(meta['type'], 'help')

    def test_mode_command(self):
        handled, output, meta = self.engine.handle_command('/mode coding')
        self.assertTrue(handled)
        self.assertIn('Coding', output)
        self.assertEqual(meta['type'], 'prefs')

    def test_mode_command_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.engine.handle_command('/mode galaxy')

    def test_name_command(self):
        handled, output, _ = self.engine.handle_command('/name Sam')
        self.assertTrue(handled)
        self.assertIn('Sam', output)

    def test_short_command_on(self):
        handled, output, _ = self.engine.handle_command('/short on')
        self.assertTrue(handled)
        self.assertIn('enabled', output)
        self.assertEqual(self.engine.preferences['short_responses'], 'true')

    def test_short_command_off(self):
        self.engine.handle_command('/short on')
        handled, output, _ = self.engine.handle_command('/short off')
        self.assertTrue(handled)
        self.assertIn('disabled', output)

    def test_short_command_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.engine.handle_command('/short maybe')

    def test_goal_command(self):
        handled, output, _ = self.engine.handle_command('/goal Finish Python course')
        self.assertTrue(handled)
        self.assertIn('Finish Python course', output)

    def test_interests_command(self):
        handled, output, _ = self.engine.handle_command('/interests math, physics')
        self.assertTrue(handled)
        self.assertIn('math', output)

    def test_profiles_command_lists_profiles(self):
        handled, output, _ = self.engine.handle_command('/profiles')
        self.assertTrue(handled)
        self.assertIn('default', output)

    def test_profile_create_command(self):
        handled, output, _ = self.engine.handle_command('/profile create work')
        self.assertTrue(handled)
        self.assertIn('work', output)
        self.assertIn('work', self.engine.list_profiles())

    def test_profile_switch_command(self):
        self.engine.create_profile('work')
        handled, output, _ = self.engine.handle_command('/profile switch work')
        self.assertTrue(handled)
        self.assertEqual(self.engine.active_profile, 'work')

    def test_profile_delete_command(self):
        self.engine.create_profile('temp')
        handled, output, _ = self.engine.handle_command('/profile delete temp')
        self.assertTrue(handled)
        self.assertNotIn('temp', self.engine.list_profiles())

    def test_task_add_command(self):
        handled, output, meta = self.engine.handle_command('/task add Buy groceries')
        self.assertTrue(handled)
        self.assertIn('Buy groceries', output)
        self.assertEqual(meta['type'], 'task')

    def test_task_list_command_empty(self):
        handled, output, _ = self.engine.handle_command('/task list')
        self.assertTrue(handled)
        self.assertIn('No tasks', output)

    def test_task_list_command_with_tasks(self):
        self.engine.add_task('Read book')
        handled, output, _ = self.engine.handle_command('/task list')
        self.assertTrue(handled)
        self.assertIn('Read book', output)

    def test_task_done_command(self):
        task = self.engine.add_task('Task to complete')
        handled, output, _ = self.engine.handle_command(f'/task done {task["id"]}')
        self.assertTrue(handled)
        self.assertIn('completed', output.lower())

    def test_task_remove_command(self):
        task = self.engine.add_task('To remove')
        handled, output, _ = self.engine.handle_command(f'/task remove {task["id"]}')
        self.assertTrue(handled)

    def test_task_clear_command(self):
        self.engine.add_task('A')
        self.engine.add_task('B')
        handled, output, _ = self.engine.handle_command('/task clear')
        self.assertTrue(handled)
        self.assertEqual(self.engine.list_tasks(), [])

    def test_task_postpone_command(self):
        task = self.engine.add_task('Task', due_date='2026-03-01')
        handled, output, _ = self.engine.handle_command(f'/task postpone {task["id"]} 7')
        self.assertTrue(handled)
        self.assertIn('2026-03-08', output)

    def test_task_edit_command(self):
        task = self.engine.add_task('Original text')
        handled, output, _ = self.engine.handle_command(
            f'/task edit {task["id"]}|Updated text|high|2027-01-01'
        )
        self.assertTrue(handled)
        self.assertIn('Updated text', output)

    def test_memory_add_command(self):
        handled, output, meta = self.engine.handle_command('/memory add Loves coding at night')
        self.assertTrue(handled)
        self.assertIn('Loves coding at night', output)
        self.assertEqual(meta['type'], 'memory')

    def test_memory_list_command(self):
        self.engine.add_memory_note('First note')
        handled, output, _ = self.engine.handle_command('/memory list')
        self.assertTrue(handled)
        self.assertIn('First note', output)

    def test_memory_clear_command(self):
        self.engine.add_memory_note('Note to clear')
        handled, output, _ = self.engine.handle_command('/memory clear')
        self.assertTrue(handled)
        self.assertEqual(self.engine.list_memory_notes(), [])

    def test_memory_recall_command(self):
        self.engine.add_memory_note('Enjoys visual learning')
        handled, output, _ = self.engine.handle_command('/memory recall visual')
        self.assertTrue(handled)
        self.assertIn('visual', output)

    def test_prefs_command_shows_preferences(self):
        handled, output, _ = self.engine.handle_command('/prefs')
        self.assertTrue(handled)
        self.assertIn('mode', output)
        self.assertIn('name', output)

    def test_reset_command(self):
        self.engine.messages.append({'role': 'user', 'content': 'hello'})
        handled, output, meta = self.engine.handle_command('/reset')
        self.assertTrue(handled)
        self.assertEqual(meta['type'], 'session')
        self.assertEqual(len(self.engine.messages), 1)  # only system prompt remains

    def test_exit_command(self):
        handled, output, meta = self.engine.handle_command('/exit')
        self.assertTrue(handled)
        self.assertEqual(meta['type'], 'exit')

    def test_unknown_command_raises(self):
        with self.assertRaises(ValueError):
            self.engine.handle_command('/doesnotexist')


class ChatLocalFallbackTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_chat_returns_string(self):
        result = self.engine.chat('What is Python?')
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_chat_blocks_unsafe_prompt(self):
        result = self.engine.chat('how to make a bomb')
        self.assertIn("can't help", result.lower())

    def test_chat_with_summarize_prefix_returns_summary(self):
        result = self.engine.chat('summarize: Python is a programming language. It is easy. It is popular.')
        self.assertIn('Local Dev Mode', result)

    def test_chat_with_plan_prefix_returns_plan(self):
        result = self.engine.chat('plan: build a web app')
        self.assertIn('Local Dev Mode', result)

    def test_chat_with_checklist_prefix_returns_checklist(self):
        result = self.engine.chat('checklist: deploy to production')
        self.assertIn('Local Dev Mode', result)

    def test_chat_injects_recalled_memory_context(self):
        self.engine.add_memory_note('User loves Python programming')
        result = self.engine.chat('Tell me about Python')
        # The user message stored in history should have embedded context
        last_user_msg = next(
            (m for m in reversed(self.engine.messages) if m['role'] == 'user'), None
        )
        self.assertIsNotNone(last_user_msg)
        self.assertIn('Memory context', last_user_msg['content'])

    def test_chat_does_not_accumulate_system_injection_messages(self):
        self.engine.add_memory_note('Prefers bullet points')
        for _ in range(3):
            self.engine.chat('Tell me about memory')
        system_count = sum(1 for m in self.engine.messages if m['role'] == 'system')
        self.assertEqual(system_count, 1)  # Only the original system prompt

    def test_chat_trims_messages_after_max(self):
        self.engine.max_messages = 6
        for i in range(10):
            self.engine.chat(f'Message {i}')
        self.assertLessEqual(len(self.engine.messages), 8)  # system + max_messages + assistant

    def test_chat_stream_returns_chunks_and_persists_assistant_message(self):
        chunks = list(self.engine.chat_stream('Tell me about Python basics'))
        self.assertTrue(chunks)
        merged = ''.join(chunks).strip()
        self.assertIn('Local Dev Mode', merged)
        self.assertEqual(self.engine.messages[-1]['role'], 'assistant')
        self.assertTrue(self.engine.messages[-1]['content'])

    def test_chat_stream_blocks_unsafe_prompt(self):
        chunks = list(self.engine.chat_stream('how to make a bomb'))
        self.assertEqual(len(chunks), 1)
        self.assertIn("can't help", chunks[0].lower())
        self.assertEqual(self.engine.messages[-1]['role'], 'assistant')

    def test_chat_falls_back_when_live_client_errors_in_dev_mode(self):
        class BrokenCompletions:
            def create(self, **_kwargs):
                raise RuntimeError('upstream auth failed')

        class BrokenChat:
            completions = BrokenCompletions()

        class BrokenClient:
            chat = BrokenChat()

        self.engine.dev_mode = True
        self.engine.client = BrokenClient()

        result = self.engine.chat('plan: prepare release')
        self.assertIn('Local Dev Mode', result)
        self.assertEqual(self.engine.messages[-1]['role'], 'assistant')
        runtime = self.engine.get_runtime_info()
        self.assertFalse(runtime['has_model'])
        self.assertEqual(runtime['mode_label'], 'local-fallback')

    def test_chat_stream_falls_back_when_live_client_errors_in_dev_mode(self):
        class BrokenCompletions:
            def create(self, **_kwargs):
                raise RuntimeError('stream failure')

        class BrokenChat:
            completions = BrokenCompletions()

        class BrokenClient:
            chat = BrokenChat()

        self.engine.dev_mode = True
        self.engine.client = BrokenClient()

        chunks = list(self.engine.chat_stream('summarize: alpha beta gamma'))
        self.assertTrue(chunks)
        merged = ''.join(chunks)
        self.assertIn('Local Dev Mode', merged)
        self.assertEqual(self.engine.messages[-1]['role'], 'assistant')
        runtime = self.engine.get_runtime_info()
        self.assertFalse(runtime['has_model'])
        self.assertEqual(runtime['mode_label'], 'local-fallback')

    def test_reset_chat_clears_history_except_system_prompt(self):
        self.engine.chat('Hello')
        self.engine.reset_chat()
        self.assertEqual(len(self.engine.messages), 1)
        self.assertEqual(self.engine.messages[0]['role'], 'system')


class ExportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_export_chat_creates_markdown_file(self):
        self.engine.chat('Hello')
        path = self.engine.export_chat()
        self.assertTrue(path.exists())
        self.assertEqual(path.suffix, '.md')
        content = path.read_text()
        self.assertIn('# Aiden Chat Export', content)

    def test_export_chat_custom_stem(self):
        path = self.engine.export_chat('my_export')
        self.assertEqual(path.stem, 'my_export')

    def test_export_chat_includes_messages(self):
        self.engine.messages.append({'role': 'user', 'content': 'Test message'})
        path = self.engine.export_chat()
        content = path.read_text()
        self.assertIn('Test message', content)


class SystemPromptTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.engine = _make_engine(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_system_prompt_contains_mode_instruction(self):
        self.engine.set_mode('coding')
        prompt = self.engine.build_system_prompt()
        self.assertIn('Coding Mode', prompt)

    def test_system_prompt_contains_name(self):
        self.engine.set_name('Alice')
        prompt = self.engine.build_system_prompt()
        self.assertIn('Alice', prompt)

    def test_system_prompt_contains_goal_when_set(self):
        self.engine.set_focus_goal('Ace the interview')
        prompt = self.engine.build_system_prompt()
        self.assertIn('Ace the interview', prompt)

    def test_system_prompt_omits_goal_when_empty(self):
        self.engine.set_focus_goal('')
        prompt = self.engine.build_system_prompt()
        self.assertNotIn('focus goal', prompt.lower())

    def test_system_prompt_contains_recent_memory_notes(self):
        self.engine.add_memory_note('Uses dark mode')
        prompt = self.engine.build_system_prompt()
        self.assertIn('Uses dark mode', prompt)

    def test_system_prompt_short_response_hint(self):
        self.engine.set_short_responses(True)
        prompt = self.engine.build_system_prompt()
        self.assertIn('concise', prompt.lower())


if __name__ == '__main__':
    unittest.main()

