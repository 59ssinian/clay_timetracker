#!/bin/bash
gunicorn main:app --workers 8 --worker-class uvicorn.workers.UvicornWorker --daemon --access-logfile ./log.logecho "The application has started."
