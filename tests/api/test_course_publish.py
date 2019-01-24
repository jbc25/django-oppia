# tests/api/test_course_publish.py
from django.test import TestCase
from django.test.client import Client

import api
from oppia.models import Course
from settings.models import SettingProperties
from django.contrib.auth.models import User

class CoursePublishResourceTest(TestCase):
    fixtures = ['user.json', 'oppia.json', 'quiz.json', 'permissions.json']
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/publish/'
        self.course_file_path = './oppia/fixtures/reference_files/anc_course.zip' 
        self.video_file_path = './oppia/fixtures/reference_files/sample_video.m4v'
        
    # test only POST is available
    def test_no_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
    
    # test all params have been sent
    def test_required_params(self):
        course_file = open(self.course_file_path,'rb') 
        
        # no username
        response = self.client.post(self.url, { 'tags': 'demo', 'password': 'secret', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 400)
        
        # no password
        response = self.client.post(self.url, { 'username': 'demo', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 400)
        
        # no tags
        response = self.client.post(self.url, { 'username': 'demo', 'password': 'secret', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 400)
        
        # no is_draft
        response = self.client.post(self.url, { 'username': 'demo', 'password': 'secret', 'tags': 'demo', api.COURSE_FILE_FIELD: course_file})
        self.assertEqual(response.status_code, 400)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
    # test tags not empty
    def test_tags_not_empty(self):
        course_file = open(self.course_file_path,'rb') 
        
        response = self.client.post(self.url, { 'username': 'admin', 'password': 'password', 'tags': '', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 400)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
    # test is user has correct permissions or not to upload
    def test_upload_permission_admin(self):
        course_file = open(self.course_file_path,'rb') 
        
        # admin can upload
        response = self.client.post(self.url, { 'username': 'admin', 'password': 'password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 201)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
      
    def test_upload_permission_staff(self):  
        #set course owner to staff
        user = User.objects.get(username='staff')
        course = Course.objects.get(shortname='anc1-all')
        course.user = user
        course.save()
        
        course_file = open(self.course_file_path,'rb') 
        # staff can upload
        response = self.client.post(self.url, { 'username': 'staff', 'password': 'password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 201)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
    def test_upload_permission_teacher(self):
        #set course owner to teacher
        user = User.objects.get(username='teacher')
        course = Course.objects.get(shortname='anc1-all')
        course.user = user
        course.save()
        
        course_file = open(self.course_file_path,'rb') 
        
        # teacher can upload
        response = self.client.post(self.url, { 'username': 'teacher', 'password': 'password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 201)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
    def test_upload_permission_user(self):
        course_file = open(self.course_file_path,'rb') 
        # normal user cannot upload
        response = self.client.post(self.url, { 'username': 'demo', 'password': 'password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 401)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
    # test user has given correct password
    def test_unauthorised_user(self):
        course_file = open(self.course_file_path,'rb')
        
        # normal user cannot upload
        response = self.client.post(self.url, { 'username': 'admin', 'password': 'wrong_password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 401)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
    # test file is correct format
    def test_file_format(self):
        
        video_file = open(self.video_file_path,'rb')
        
        # send video file instead
        response = self.client.post(self.url, { 'username': 'admin', 'password': 'password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: video_file })
        self.assertEqual(response.status_code, 400)
        
        video_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
    # test if user is trying to overwrite course they don't already own
    def test_overwriting_course_non_owner(self):
        #set course owner to admin
        user = User.objects.get(username='admin')
        course = Course.objects.get(shortname='anc1-all')
        course.user = user
        course.save()
        
        course_file = open(self.course_file_path,'rb')
        
        # teacher attempts to update
        response = self.client.post(self.url, { 'username': 'teacher', 'password': 'password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 401)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
    
    # check file size of course
    def test_course_filesize_limit(self):
        setting = SettingProperties.objects.get(key='MAX_UPLOAD_SIZE')
        setting.int_value = 1000
        setting.save()
        
        course_file = open(self.course_file_path,'rb')
        
        response = self.client.post(self.url, { 'username': 'admin', 'password': 'password', 'tags': 'demo', 'is_draft': False, api.COURSE_FILE_FIELD: course_file })
        self.assertEqual(response.status_code, 400)
        
        course_file.close() # shouldn't be strictly necessary to close the file, but avoids ResourceWarnings about unclosed files
        
        
    # TODO - check overwriting course with older version
    
    