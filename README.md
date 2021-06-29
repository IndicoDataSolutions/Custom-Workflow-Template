# Custom-Workflow-Template
template for a custom workflow


## Things you'll need:

* You will need access to Indico's codeship account: https://app.codeship.com/
* Install the codeship CLI
* You will need access to Indico's GCP compute engine manager
* You will need access to Asana to retrieve cluster manager pem and IP.
* You will need Indico VPN access.



## Setting up your workflow repo:

1. Use this repository as a template for your project code. Replacing "custom_app", anywhere it appears, with your app name.
2. Create a codeship project and download the project's AES key (link the project with your github repo).
3. Three of the files are encrypted 'dockercfg.encrypted', 'codeship.env', and 'build_args.encrypted'- 
these are encrypted using the metlife-funding-memos project AES key- use that key to decrypt the files
and then re-encrypt them using the AES key you downloaded in the previous step. `jet encrypt|decrypt $FILENAME` 
(NOTE: don't actually commit your AES key to your repository)

4. Find the filepath to your model ID (this will have to change every time the model is updated).
   `kube exec moonbow` then run the script 'get_model_paths.py', you'll see it in the scripts folder.
   Add this in your workflow.py pred_kwargs for model_file_path.

5. Incorporate your custom code into workflow.py.

6. Test that the workflow works locally using either `jet steps` or `jet run YOUR-PROJECT-tests`
   (note: if you run `jet run` run `jet cleanup` afterwards)

## Deploying your Custom Workflow:

Step 1: successfully build repo on codeship. (happns automatically )

Step 2: get image hash from google container registry ( hash is under "tags" in the table)

Step 3: go to cluster manager of the VPC you want to deploy to (can find details under asana indico installations board, access via `ssh cluster_name` after you've registered pem/IP to .ssh/config)

Step 4: run `indico updraft edit -I`

Step 5: add image (image-name and image-hash are both derived from GCP)
 images:
   {name-of-image}: {image-name}:{image-hash}

Step 6: add new service:
services:
  {service-name}:
    <!template>: appstack
    app: {python_lib_name}
    # env is optional
    env: 
    - name: QUEUE_NAME
      value: '1231231'
    # name-of-image is whatever you called name-of-image in step 5
    image: {name-of-image}
    queue: {queue-name}
    type: celery
    values:
      resources:
        memory: 4Gi

Step 7: Save + render with changes, but * do NOT apply when prompted

Step 8: indico render  {service-name}

Step 9: open the generated file in the generated/ folder and check the image name

Step 10: wait until the container is listed as ready (watch -n 2 kp {service-name})

Step 11: create an empty dataset to attach the workflow to in the Indico UI

Step 12: get your user ID from the admin screen in the UI

Step 13: get queue and task name from JS.task definition in your repository

Step 14: run custom workflow creation script (in elnino container ./scripts directory, to access: `kube exec elnino`)

Step 15: write your workflow ID down!



To update to a new image (after committing to your github main branch), run this command from the cluster 
manager:
`indico push image_name service_name image_name:IMAGE_HASH`
The workflow will be updated immediately and no other changes will be needed.

Or edit indico updraft and manually replace the hash, render all but don't apply. indico apply service_name

Things not working?

* From the cluster: `klogs start_of_your_worker_or_service_name` 


Nice to haves: 

painful point is having to grab the model paths from the cluster. Need to be able to get that info 
via the api.

Ability to test the JS task with real data (possibly cached somewhere from API call)