from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author_user')
        cls.not_author = User.objects.create(username='Not_author_user')
        cls.note = Note.objects.create(
            title='title',
            text='text',
            slug='slug',
            author=cls.author
        )

    def test_list_page_have_notes_objects(self):
        self.notes = Note.objects.bulk_create(
            Note(title='title',
                 text='text',
                 slug=f'slug{index}',
                 author=self.author)
            for index in range(5)
        )

        for client, instance in (
            (self.client.force_login(self.author), Note),
            (self.client.force_login(self.not_author), None)
        ):
            for note in self.client.get(
                    reverse('notes:list')).context['object_list']:
                with self.subTest(note=note):
                    self.assertIsInstance(note, instance)

    def test_form_access(self):
        self.client.force_login(self.author)
        for name, arg in (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        ):
            with self.subTest(name=name, arg=arg):
                response = self.client.get(reverse(name, args=arg))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
