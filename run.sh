#!/bin/bash
gunicorn "apps:create_app('config.ProductionConfig')"
