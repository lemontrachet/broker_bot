from __future__ import absolute_import, unicode_literals
from celery import Celery

app = Celery('proj',
             broker='amqp://mld:raspbian@192.168.0.3/vhost1',
             backend='amqp://mld:raspbian@192.168.0.3/vhost1',
             include=['proj.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
