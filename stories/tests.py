from django.test import TestCase
from django.test.client import Client

from stories.models import Project, Story


class SimpleTest(TestCase):

    urls = 'stories.urls'
    fixtures = ['test.json',]

    def setUp(self):
        "Set up test data"
        self.client = Client()
        self.projects = Project.objects.all()
        self.active_projects = Project.objects.filter(active=True)
        self.unactive_projects = Project.objects.filter(active=False)

    def test_fixtures(self):
        "Test fixtures are loaded and data is accessible"
        self.assertNotEqual(self.projects.count(), 0)

    def test_index(self):
        "Test the loading of index page"
        # Make request and assure status code
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Test for full content being provided
        self.assertEqual(
            len(response.context['projects']), self.active_projects.count()
        )
        # Test for provided data to view
        self.assertTemplateUsed(response, 'index.html')
        self.assertTemplateNotUsed(response, 'project.html')
        for project in self.active_projects:
            self.assertContains(response, project.name, 1)
        for project in self.unactive_projects:
            self.assertNotContains(response, project.name)

    def test_add_project(self):
        "Test the add project page"
        # Get the projects length before saving
        old_projects = self.projects.count()
        # Add project should be a post only page
        response_fail = self.client.get('/add/')
        self.assertEqual(response_fail.status_code, 404)
        # Test a non valid form
        name_fail = 'Tchululu'
        response_fail = self.client.post('/add/', {'name':name_fail})
        self.assertEqual(response_fail.status_code, 200)
        self.assertContains(response_fail, name_fail)
        # Testing a post form
        name_added = 'Tchululu'
        desc_added = 'Lorem ipsum dolor sit amet.'
        response = self.client.post('/add/', 
                {'name':name_added, 'description':desc_added}
        )
        self.assertRedirects(response, '/')
        # Test database have actually been updated and check new content
        new_projects = Project.objects.all().count()
        self.assertNotEqual(old_projects, new_projects)
        added_project = Project.objects.get(name=name_added)
        self.assertEqual(added_project.description, desc_added)

    def test_remove_project(self):
        "Test removing project"
        # Get the projects length before saving
        old_projects = self.projects.count()
        # Add project should be a post only page
        response_fail = self.client.get('/remove/')
        self.assertEqual(response_fail.status_code, 404)
        # Test a non valid form
        response_fail = self.client.post('/remove/', {'delete_id':'20'})
        self.assertEqual(response_fail.status_code, 404)
        # Testing a post form
        id_deleted = '1'
        response = self.client.post('/remove/', {'delete_id':id_deleted})
        self.assertRedirects(response, '/')
        # Test database have actually been updated and check new content
        new_projects = Project.objects.filter(active=True)
        self.assertNotEqual(old_projects, new_projects.count())
        for project in new_projects:
            self.assertNotEqual(project.id, id_deleted)

    def test_project_page(self):
        "Test the project index page"
        # Test non existing page
        response_fail = self.client.get('/project/9999/')
        self.assertEqual(response_fail.status_code, 404)
        # Test unactive pages
        for project in self.unactive_projects:
            response_fail = self.client.get('/project/'+str(project.id)+'/')
            self.assertEqual(response_fail.status_code, 404)
        # Test active pages
        for project in self.active_projects:
            response = self.client.get('/project/'+str(project.id)+'/')
            self.assertEqual(response.status_code, 200)
            # Check for page's content
            for story in project.story_set.all():
                self.assertContains(response, story.name)
                self.assertContains(response, story.time)

    def test_change_story_time(self):
        "Test the form to update a story time"
        # Should be a post only page
        response_fail = self.client.get('/change_story_time/')
        self.assertEqual(response_fail.status_code, 404)
        # Test a non valid form
        response_fail = self.client.post('/change_story_time/', {'id':'20'})
        self.assertEqual(response_fail.status_code, 404)
        # Testing a post form
        for project in self.active_projects:
            for story in project.story_set.all():
                old_story_time = story.time
                new_story_time = 24
                response = self.client.post('/change_story_time/',
                        {'id':story.id, 'time':new_story_time,}
                )
                self.assertRedirects(response, '/project/'+str(project.id)+'/')
                new_story = Story.objects.get(id=story.id)
                self.assertNotEqual(old_story_time, new_story.time)
                self.assertEqual(new_story.time, new_story_time)
