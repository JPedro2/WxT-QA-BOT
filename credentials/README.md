## GCP Credentials
Move your GCP Service Account Key `.json` file here. This file is used by the `backend-api` container to [authenticate with the GCP account](https://cloud.google.com/docs/authentication/production#passing_the_path_to_the_service_account_key_in_code) and allow uploading files to GCP Cloud Storage.

Please check here for more information on [how to get your service account key](https://cloud.google.com/docs/authentication/production#obtaining_and_providing_service_account_credentials_manually).

**After you move the Service Account Key file to this folder you MUST rename it to:** `GCP-serviceAcctKey.json`