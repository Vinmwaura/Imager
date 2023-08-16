#!/bin/bash
gunicorn 'apps:create_app()'
