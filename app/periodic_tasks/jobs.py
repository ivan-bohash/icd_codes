from app.scraper.pagination import run_pagination_parser
from app.scraper.urls import run_urls_parser
from app.scraper.history import run_history_parser

cron_string = "* * * * *"

scheduler_jobs = [
    # List of jobs where next job runs when previous is finished

    # pagination
    {
       "func": run_pagination_parser,
       "cron_string": cron_string,
       "args": None,
       "depends_on": None,
    },
    # urls update
    {
        "func": run_urls_parser,
        "cron_string": cron_string,
        "args": ["update"],
        "depends_on": "run_pagination_parser",
    },
    # urls delete
    {
        "func": run_urls_parser,
        "cron_string": cron_string,
        "args": ["delete"],
        "depends_on": "run_urls_parser_update",
    },
    # history
    {
        "func": run_history_parser,
        "cron_string": cron_string,
        "args": None,
        "depends_on": "run_urls_parser_delete",
    },
]




