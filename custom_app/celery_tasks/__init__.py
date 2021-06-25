from jetstream.app import JetFlow

IMPORTS = [
    "custom_app.celery_tasks.workflow"
]

# you create the name here
JS = JetFlow("custom_app", include=IMPORTS, imports=IMPORTS)

CELERY_APP = JS.celery_app