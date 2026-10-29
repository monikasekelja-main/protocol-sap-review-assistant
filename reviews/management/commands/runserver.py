"""Keep local uploads moving with the development web server."""

import os
import subprocess
import sys

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command as Runserver


class Command(Runserver):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--no-worker", action="store_true", help="Use a separately managed review worker."
        )

    def handle(self, *args, **options):
        # The autoreloader's parent owns the worker across web process reloads.
        if not settings.DEBUG or options["no_worker"] or os.environ.get("RUN_MAIN") == "true":
            return super().handle(*args, **options)
        worker = subprocess.Popen(
            [sys.executable, str(settings.BASE_DIR / "manage.py"), "review_worker"],
            cwd=settings.BASE_DIR,
        )
        self.stdout.write("Starting the local review worker alongside the web server.")
        try:
            return super().handle(*args, **options)
        finally:
            worker.terminate()
            worker.wait()
