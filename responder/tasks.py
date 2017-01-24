from __future__ import absolute_import, unicode_literals
from .celery import app

@app.task
def respond(text, tw_id):
    from response_engine import Tweet_Builder
    tb = Tweet_Builder()
    return tb.respond(text, tw_id)

