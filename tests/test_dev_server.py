import os
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from reviews.management.commands.runserver import Command


@override_settings(DEBUG=True)
class DevelopmentServerTests(SimpleTestCase):
    @patch.dict(os.environ, {"RUN_MAIN": "false"})
    @patch("reviews.management.commands.runserver.subprocess.Popen")
    @patch("reviews.management.commands.runserver.Runserver.handle")
    def test_worker_is_started_and_stopped_with_server(self, serve, spawn):
        Command().handle(no_worker=False)
        self.assertEqual(spawn.call_args.args[0][-1], "review_worker")
        spawn.return_value.terminate.assert_called_once()
        spawn.return_value.wait.assert_called_once()
        serve.assert_called_once()

    @patch.dict(os.environ, {"RUN_MAIN": "false"})
    @patch("reviews.management.commands.runserver.subprocess.Popen")
    @patch("reviews.management.commands.runserver.Runserver.handle", side_effect=SystemExit)
    def test_worker_stops_if_server_exits(self, serve, spawn):
        with self.assertRaises(SystemExit):
            Command().handle(no_worker=False)
        spawn.return_value.terminate.assert_called_once()
        spawn.return_value.wait.assert_called_once()

    @patch("reviews.management.commands.runserver.subprocess.Popen")
    @patch("reviews.management.commands.runserver.Runserver.handle")
    def test_reloader_child_and_separate_worker_do_not_spawn_duplicates(self, serve, spawn):
        with patch.dict(os.environ, {"RUN_MAIN": "true"}):
            Command().handle(no_worker=False)
        Command().handle(no_worker=True)
        with override_settings(DEBUG=False):
            Command().handle(no_worker=False)
        spawn.assert_not_called()
