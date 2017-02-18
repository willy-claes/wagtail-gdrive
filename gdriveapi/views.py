import os
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response

from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
from apiclient.discovery import build

from django import VERSION as DJANGO_VERSION
from django.db.models import Q
from django.utils.text import slugify

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.rich_text import DbWhitelister
from gdriveapi.models import SyncMeta
from blog.models import BlogIndexPage, BlogPage

class SyncView(APIView):
    def __init__(self):
        # Get the page class.
        self.page_class = BlogPage

        # Get the parent page.
        self.parent_page = BlogIndexPage.objects.get()

        # Instantiate Google Drive API helper.
        self.drive_service = self.__get_drive_service()

    def get(self, request, format=None):
        changes = self.__retrieve_changes()
        for change in changes:
            self.__update_page(change['id'], change['name'], change['modified_at'])

        return Response(str(len(changes)) + ' files changed.')

    def __get_drive_service(self):
        """
        Create Google Drive API service.
        """
        scopes = ['https://www.googleapis.com/auth/drive']
        json_file = os.path.dirname(os.path.realpath(__file__)) + '/wagtail.json'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file, scopes=scopes)
        http_auth = credentials.authorize(Http())
        return build('drive', 'v3', http=http_auth)

    def __get_change_page_token(self):
        """
        Get the starting page token for listing next changes.
        """
        # FIXME: Do not pass a default value.
        page_token = SyncMeta.get_value('start_page_token', '1')

        if page_token is False:
            response = self.drive_service.changes().getStartPageToken().execute()
            page_token = response.get('startPageToken')
            SyncMeta.set_value('start_page_token', page_token)

        return page_token

    def __retrieve_changes(self):
        changes = []
        page_token = self.__get_change_page_token()
        while True:
            response = self.drive_service.changes().list(
                    fields='changes(file(id,name,mimeType,modifiedTime)),nextPageToken,newStartPageToken',
                    pageToken=page_token
                ).execute()

            for change in response.get('changes', []):
                # We handle only Google Docs files at the moment.
                file = change.get('file')
                if file.get('mimeType') == 'application/vnd.google-apps.document':
                    modified_at = file.get('modifiedTime')
                    modified_at = datetime.strptime(modified_at[:19], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')

                    changes.append({
                        'id': file.get('id'),
                        'name': file.get('name'),
                        'modified_at': modified_at
                    })

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                SyncMeta.set_value('start_page_token', response.get('newStartPageToken'))
                break

        return changes

    def __get_resource(self, file_id):
        """
        Export the resource with given ID to HTML.
        """
        return self.drive_service.files().export(fileId=file_id, mimeType='text/html').execute()

    def __update_page(self, file_id, title, date):
        """
        Update page with the given title, date and body.
        """

        # Retrieve file contents.
        body = self.__get_resource(file_id)

        # Get the page class.
        page_class = self.page_class

        # Get the parent page.
        parent_page = self.parent_page

        # Determine whether to add new page or update existing one.
        existing = SyncMeta.get_value('file:' + file_id)
        if not(existing is False):
            page = page_class.objects.get(pk=existing)
            page.date = date
            page.body = DbWhitelister.clean(body)
            page.save()
            return

        # Create an empty page.
        page = page_class();

        # Get the form class.
        form_class = page_class.get_edit_handler().get_form_class(page_class)

        # Instantiate a form class.
        form = form_class(data={
            'title': title,
            'date': date,
            'body': body,
            'slug': self.__generate_slug(title, parent_page)
        }, instance=page, parent_page=parent_page)

        if form.is_valid():
            page = form.save(commit=False)
            parent_page.add_child(instance=page)

            # Keep the synced matches.
            SyncMeta.set_value('file:' + file_id, page.id)

    def __generate_slug(self, title, parent_page, page=None):
        """
        Generate a slug from the given title.
        """
        if DJANGO_VERSION >= (1, 9):
            base_slug = slugify(title, allow_unicode=True)
        else:
            base_slug = slugify(title)

        slug = base_slug
        suffix = 1

        while not self.__slug_is_available(slug, parent_page, page):
            suffix += 1
            slug = "%s-%d" % (base_slug, suffix)

        return slug

    def __slug_is_available(self, slug, parent_page, page=None):
        """
        Determine whether the given slug is available for use on a child page of
        parent_page. If 'page' is passed, the slug is intended for use on that page
        (and so it will be excluded from the duplicate check).
        """
        if parent_page is None:
            # The root page's slug can be whatever it likes.
            return True

        siblings = parent_page.get_children()
        if page:
            siblings = siblings.exclude(Q(id=page.id))

        return not siblings.filter(slug=slug).exists()
