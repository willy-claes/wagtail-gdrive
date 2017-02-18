# wagtail-gdrive
Sync resources between Wagtail CMS and Google Drive

## Configuration
1. Go to the Google API Console, create a new project and enable Google Drive API.

2. Create a new credential of service account key. Enter the service account name and select a role as project owner. Be sure to choose the key type as JSON. Keep the JSON file downloaded in a secure place, you won't be able to re-generate it. It is used to authenticate API requests afterwards. Also please keep the service account ID.

3. Go to your Google Drive. Assuming that you have a folder containing all files to be synced with your Wagtail site, share the folder with the service account created in the previous step.

4. On your server, install the Google API client library.

  `pip install --upgrade google-api-python-client`

5. Copy the package to your site. And copy the credentials JSON file you downloaded in step 2 to the package folder. Rename it as `wagtail.json`.

6. Add `gdriveapi` to the `INSTALLED_APPS` in settings file.

7. Run migrations.

  `./manage.py makemigrations gdriveapi`

  `./manage.py migrate`

8. Open `urls.py` and add the following record to `urlpatterns`.

  `url(r'^gdriveapi/', include('gdriveapi.urls'))`

9. Specify the page class for files imported from Google Drive and the parent page to keep all these pages in `views.py`.

10. Access the url endpoint to start watching and syncing files.

  `GET https://your-site-url/gdriveapi/sync`

11. Check if the files on Google Drive are imported correctly. Add or update files on Google Drive and check if changes are synced correctly. (It might take a few minutes for Google Drive API to detect changes, so please re-try it a few minutes later if you don't see any changes on your site.)

12. You can create a cron job accessing the url endpoint periodically.
