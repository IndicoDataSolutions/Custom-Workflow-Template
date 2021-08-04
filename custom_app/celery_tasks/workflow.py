from uuid import uuid4

from custom_app.celery_tasks import JS
from jetstream.contexts import Ctx, CKey
from jetstream.tasks import Task, Chain
from indicore.enums import TaskType, ModelType, FeatureDomainEnum
from jetstream.plugins.storage.storage_object import StorageObject



def load_context_values(task, ctx_mappings):
    """
    Retrieve your submissions filename, full text, and ocr storage object
    """
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


# BEGINNING OF CUSTOM WORKFLOW: start extraction pipeline is the beginning of your custom workflow.
# You are intercepting post-OCR and beginning your sequence of models and logic.
@JS.task(
    "start_extraction_pipeline",
    # queue is a name you create for your worker, it should be identical across your tasks
    queue="my_workflow_name",
    # trail_ctx are the context arguments that follow the process as it moves between tasks
    trail_ctx=True,
)
def start_extraction_pipeline(
    task, ctx_mappings: CKey("workflow", "ctx_mappings") = None
):
    ctx_values = load_context_values(task, ctx_mappings=ctx_mappings)
    ocr_text = ctx_values["text"]
    # other values you have here, not used in this example yet
    print(ctx_values["filename"])
    # you need to load the ocr object
    print(task.storage.read_store_object(ctx_values["ocr_storage"]))

    # this example is starting off with a classification model, the kwargs are model type specific
    kwargs = {
        # model_id isn't actually used but should be accurate for record keeping
        "model_id": 631,
        "model": {
            "id": 631,
            # you will get your actual model_file_path from the cluster,
            # this will need to be updated everytime the model changes.
            "model_file_path": "/finetune_models/e52e5884-d46b-11eb-8382-7ecdc26c016d",
            # these are standard for classification models
            "task_type": TaskType.CLASSIFICATION,
            "model_type": ModelType.STANDARD,
            "model_options": {},
            "status": "complete",
            "user_id": 1,
        },
        "model_options": {
            "domain": FeatureDomainEnum.STANDARD_V2,
        },
        "model_group": {
            # these don't matter can be anything
            "subset_id": 1,
            "dataset_id": 1,
        },
        "sequence": False,
        "save_to_db": False,
        "load_existing_data": False,
        "vectors_key": str(uuid4())
    }
    # NOTE: if you wanted to run some tasks in parallel, wrap Task(), Task() in Group() -> List[List]
    return Chain(
        # this cyclone featurize task is boiler plate for running classification
        Task("cyclone", "featurize", "start", kwargs={**kwargs, "data": [ocr_text]}),
        # this is boilerplate for a classification task
        Task(
            "customv1",
            "predict_classification",
            "predict",
            kwargs=kwargs,
        ),
        # for classification, we want to then pass to this "router" to pass to different models based on result
        Task(
            # below should match you app name in the __init__.py of this module
            # order is app, queue, path (reverse of JS.Task)
            "custom_app", #this should match __init__.py name and needs to match the name of the service in updraft
            "my_workflow_name",
            "doc_type_router",
            kwargs={"ocr_text": [ocr_text]},
        ),
        # post_processing is part of chain in doc_type_router
    )



# This matches the last task above
@JS.task("doc_type_router", queue="my_workflow_name", trail_ctx=True)
def doc_type_router(
    task,
    classification_result: List[dict], # this is passed automatically into this task
    ocr_text: List[str],
):
    # if you want to store something for later, store it like this (here key is 'clf_results')
    # you will specify this as an arg later with CKey, see post_processing function
    task.ctx_holder.update(
        CKey("workflow", "clf_results"),
        classification_result,
    )
    # below are the standard kwargs for an extraction model
    extraction_kwargs = {
        # use your actual model id for record keeping, but doesn't matter
        "model_id": 663,
        "model": {
            "id": 663,
            # look up your actual model filepath in the DB
            "model_file_path": "/finetune_models/ede8b152-e007-11eb-b469-e6b58bf8c967",
            "task_type": TaskType.ANNOTATION,
            "model_type": ModelType.FINETUNE,
            "model_options": {},
            # user_id can be anything
            "user_id": 1,
        },
    }

    # You could then use some logic based on "classification_result" to alter the kwargs
    # to select a different model (change model_file_path), etc.
    if classification_result: # some actual logic
        extraction_kwargs["model"]["model_file_path"] = ""
    else:
        extraction_kwargs["model"]["model_file_path"] = ""
    return Chain(
        Task(
            # This is always the same for extraction model
            "customv2",
            "predict",
            "predict",
            args=(ocr_text,),  # ocr_text List[str]
            kwargs=extraction_kwargs,
        ),
        # finally passing this to our final task
        Task("funding_memos", "my_workflow_name", "post_processing"),
    )


@JS.task("post_processing", queue="my_workflow_name", trail_ctx=True)
def post_processing(
    task,
    extractions, # if you use Group(Task, Task) this is a list of length # of models
    ctx_mappings: CKey("workflow", "ctx_mappings") = None,
    # if you want to retrieve something you saved earlier, include it as an arg with the CKey specified
    cls_preds: CKey("workflow", "clf_results") = None,  # List[dict]
):
    # result from previous task (in this case extractions)
    print(extractions[0])
    ctx_values = load_context_values(task, ctx_mappings=ctx_mappings)
    # your OCR object
    print(task.storage.read_store_object(ctx_values["ocr_storage"]))
    # filename
    print(ctx_values["filename"])
    # INSERT WHATEVER CUSTOM LOGIC YOU WANT TO APPLY TO OUTPUT
    myoutput_dict = {}
    # create a name for your output file, should use this uuid4 for json output
    result_prefix = uuid4()
    # Create your final output json like below and return it
    result_obj = task.storage.store(
        myoutput_dict,
        meta=True,
        filename=f"{result_prefix}.json",
        serializer="json",
    )
    return result_obj
