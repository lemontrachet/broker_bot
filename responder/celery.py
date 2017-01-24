from __future__ import absolute_import, unicode_literals
from celery import Celery

app = Celery('responder',
             broker='amqp://mld:raspbian@192.168.0.2/vhost1',
             backend='amqp://mld:raspbian@192.168.0.2/vhost1',
             include=['responder.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()

