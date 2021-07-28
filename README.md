# Custom-Workflow-Template
template for a custom workflow


## Things you'll need:

* You will need access to Indico's codeship account: https://app.codeship.com/
* Install the codeship CLI / Docker
* You will need access to Indico's GCP compute engine manager
* You will need access to Asana to retrieve cluster manager pem and IP.
* You will need Indico VPN access.



## Setting up your workflow repo:

1. Use this repository as a template for your project code. Replacing "custom_app", anywhere it appears, with your app name. The key elements of your custom workflow will be present in the celery_tasks module.

2. Create a codeship project and download the project's AES key (link the project with your github repo).

3. Three of the files are encrypted 'dockercfg.encrypted', 'codeship.env', and 'build_args.encrypted'- 
these are encrypted using the metlife-funding-memos project AES key- use that key to decrypt the files
and then re-encrypt them using the AES key you downloaded in the previous step. `jet encrypt|decrypt $FILENAME` 
(NOTE: don't actually commit your AES key to your repository)

4. Find the filepath to your model ID (this will have to change every time the model is updated).
   `kube exec moonbow` then create a script `get_model_paths.py` in the scripts folder there, 
   that mirrors the `get_model_paths.py` script in this repo's scripts folder. Run the script
   using two args that are a range of model IDs (e.g. use 164 164 if you want path to model ID 164)
   Add this filepath to the workflow.py pred_kwargs for model_file_path in this repo's celery_tasks module. 

5. Incorporate your custom code into workflow.py.

6. Test that the workflow works locally using either `jet steps` or `jet run YOUR-PROJECT-tests`
   (note: if you run `jet run` run `jet cleanup` afterwards)

## Deploying your Custom Workflow:

Step 1: successfully build repo on codeship. (happns automatically when you push your code to github)

Step 2: get image hash from google container registry (hash is under "tags" in the table) This looks like: 
        `main.a5499e0b92e9ec890c91fb90e0a7b5eff9888f05`

Step 3: go to cluster manager of the VPC you want to deploy to (can find details under asana indico installations board, access via `ssh cluster_name` after you've registered pem/IP to .ssh/config)

Step 4: run `indico updraft edit -I`

Step 5: add image (image-name and image-hash are both derived from GCP- image-name will be present on the   
        page like `gcr.io/new-indico/metlife-funding-memos` name = metlife-funding-memos). "name-of-image"
        will be somethiing you can make up to reference the image when you set up the service in next step.
        The image will appear in the updraft config like:
```
 images:
   {name-of-image}: {image-name}:{image-hash}
```

Step 6: add new service:
```
services:
  # this is what your service will be called
  {service-name}:
    <!template>: appstack
    app: {python_lib_name}
    # env is optional if you have multiple QUEUES on same cluster (i.e a QA/DEV)
    env: 
    - name: QUEUE_NAME
      value: '1231231'
    # name-of-image is whatever you called name-of-image in step 5
    image: {name-of-image}
    # queue-name is whatever you call your queue in workflow.py
    queue: {queue-name}
    type: celery
    values:
      resources:
        memory: 4Gi
```
Step 7: Save and then select "y" render with changes, but do NOT NOT NOT apply when prompted, select "No"

Step 8: Run `indico render {service-name}` to creat a .yaml file for the service you created.

Step 9: open the generated file in the generated/ folder and check the image name to make sure it looks 
        like: `gcr.io/new-indico/metlife-funding-memos:main.a5499e0b92e9ec890c91fb90e0a7b5eff9888f05`

Step 9.1: Run `indico apply {service-name}`.

Step 10: Wait until the container is listed as ready (watch -n 2 kp {service-name}). Once it is started, 
         the service is running. If you are just updating the image, you are finished and can call your 
         workflow. If you haven't attached the service to a workflow, continue to step 11. 

Step 11: Create a dataset to attach the workflow to in the Indico UI.

Step 12: Get your user ID from the admin screen in the UI.

Step 13: Get the queue and task name from `JS.task` definition in your repository's celery_tasks module.

Step 14: run custom workflow creation script (in elnino container ./scripts directory, to access:
         `kube exec elnino`) and follow the instructions. 

Step 15: write your workflow ID down!



An alternative way to update to a new image (after committing to your github main branch), run this command 
from the cluster manager:
`indico push image_name service_name image_name:IMAGE_HASH`
The workflow will be updated immediately and no other changes will be needed. You can only do this if you 
have one custom service, if you have two (that use same image), you'll need to follow steps above.

Things not working?

* From the cluster: `klogs start_of_your_worker_or_service_name`
* From the cluster: `klogs service_name\|customv2\|customv1\|doctor-workflow\|etc.` for all services used and then run a 
                     doc through workflow. 
* From the cluster: `kubectl describe pod name-of-service`
* You can `kube exec service-name` and then make changes to your code that will apply instantly to you 
  workflow for debugging. After making the changes type `cerleryd restart`. You should of course then make 
  fixes to your actual code and then apply a new image. If you want to revert any changes that you made,
  you can run `kube update service-name` to undo your code changes.
