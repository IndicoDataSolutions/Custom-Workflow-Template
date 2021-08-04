from jetstream.app import JetFlow

IMPORTS = [
    "custom_app.celery_tasks.workflow"
]

# create a name for your app here, i.e. replace "custom_app"
JS = JetFlow("custom_app", include=IMPORTS, imports=IMPORTS)

CELERY_APP = JS.celery_app