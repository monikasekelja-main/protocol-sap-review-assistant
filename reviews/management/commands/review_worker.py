import time

from django.core.management.base import BaseCommand

from reviews.jobs import process_next


class Command(BaseCommand):
    help = "Process queued reviews. SQLite development supports one worker only."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            processed = process_next()
            if options["once"]:
                break
            if not processed:
                time.sleep(2)
