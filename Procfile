# Heroku Procfile
# Defines process types for Heroku deployment

web: gunicorn --config gunicorn.conf.py wsgi:application
worker: python orbcomm_scheduler.py
release: python -c "from orbcomm_tracker.database import Database; Database().create_tables()"
