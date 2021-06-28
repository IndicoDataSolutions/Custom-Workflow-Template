from uuid import uuid4

from custom_app.celery_tasks import JS
from jetstream.contexts import Ctx, CKey
from jetstream.tasks import Task, Chain
from indicore.enums import TaskType, ModelType


def load_context_values(task, ctx_mappings):
    ocr_storage_obj = None
    filename = None
    text = None
    for ctx_mapping in ctx_mappings:
        for context in ctx_mapping.values():
            context_values = task.ctx_holder.get_all(context.store_key)
            if "filenames" in context_values:
                filename = context_values["filenames"][0]
            if "etl_outputs" in context_values:
                ocr_storage_obj = context_values["etl_outputs"][0]
            if "rows" in context_values and "etl_outputs" not in context_values:
                # The rows with etl outputs and rows is a duplicate of etl output -
                # the other is just the text that we want.
                text = context_values["rows"][0]
    return {
        "filename": filename,
        "text": text,
        "ocr_storage": ocr_storage_obj,
    }


# Below assume you are intercepting the OCR and just passing it to an extraction model
# queue is the name of your worker, it is append to your app name
# trail_ctx is the context arguments that follow the process as it moves between tasks on the custom chain
@JS.task(
    "start_extraction_pipeline", queue="workflow", trail_ctx=True
)
def start_extraction_pipeline(
    task, ctx_mappings: CKey("workflow", "ctx_mappings") = None
):
    ctx_values = load_context_values(task, ctx_mappings=ctx_mappings)
    ocr_text = ctx_values["text"]
    predict_kwargs = {
        "model_id": 12345,  # not used, but probably should be accurate
        "model": {
            "id": 12345,  # not used, but probably should be accurate
            #IMPORTANT model_file_path to be grabbed from the cluster and updated everytime the model changes.
            "model_file_path": "", 
            "task_type": TaskType.ANNOTATION,
            "model_type": ModelType.FINETUNE,
            "model_options": {},
            # set a user id for logging here
            "user_id": 1,
        },
    }
    # NOTE: if you wanted to run in parallel, wrap Task(), Task() in Group() -> List[List]
    return Chain(
        Task(
            # This needs to specify the actual IPA process that will be run
            "customv2",
            "predict",
            "predict",
            args=([ocr_text],),
            kwargs=predict_kwargs,
        ),
        # order is app, queue, path (reverse of JS.Task)
        # below should match you app name in the __init__.py of this module
        Task("custom_app", "workflow", "post_processing"),
    )


@JS.task("post_processing", queue="workflow", trail_ctx=True)
def post_processing(
    task, chain_output, ctx_mappings: CKey("workflow", "ctx_mappings") = None
):
    # Predictions is automatically populated by the chain.
    # List[dict] predictions List[] == 2 if 2 grouped tasks
    extractions = chain_output[
        0
    ]
    ctx_values = load_context_values(task, ctx_mappings=ctx_mappings)
    tokens = task.storage.read_store_object(ctx_values["ocr_storage"])
    input_filename = ctx_values["filename"]
    # task.storage.store if larger than 100mb, not relevant here
    result_prefix = uuid4()
    return task.storage.store(
        dict, # this should be your result object 
        meta=True, 
        filename=f"{result_prefix}.json", 
        serializer="json",
    )
