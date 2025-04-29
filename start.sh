#!/bin/bash
export PORT=10000
export WEB_CONCURRENCY=1
gunicorn main:app --bind 0.0.0.0:$PORT
