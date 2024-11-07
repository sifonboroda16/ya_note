from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from pytils.translit import slugify
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()

TITLE_FIELD = 'title'
TEXT_FIELD = 'text'
SLUG_FIELD = 'slug'


class TestLogicCreate(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author_user')
        cls.not_author = User.objects.create(username='Not_Author_user')
        cls.form_data = dict(
            title=TITLE_FIELD,
            text=TEXT_FIELD,
            slug=SLUG_FIELD
        )

    def test_author_can_create_note(self):
        self.client.force_login(self.author)
        self.client.post(reverse('notes:add'), data=(self.form_data))
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(
            (note.title, note.text, note.slug),
            (TITLE_FIELD, TEXT_FIELD, SLUG_FIELD)
        )

    def test_anonymous_cant_create_note(self):
        self.client.post(reverse('notes:add'), data=(self.form_data))
        self.assertEqual(Note.objects.count(), 0)


class TestLogicEditDate(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author_user')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author = User.objects.create(username='Not_Author_user')
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        cls.note = Note.objects.create(
            title=TITLE_FIELD,
            text=TEXT_FIELD,
            slug=SLUG_FIELD,
            author=cls.author,
        )
        cls.slug_arg = (cls.note.slug,)
        cls.new_title = 'edited title'
        cls.new_text = 'edited text'
        cls.new_slug = 'edited-slug'
        cls.form_data = dict(
            title=cls.new_title,
            text=cls.new_text,
            slug=cls.new_slug
        )
        cls.note_attrs = (cls.note.title, cls.note.text, cls.note.slug),
        cls.note_updated_attrs = (cls.new_title, cls.new_text, cls.new_slug)

    def test_slugify(self):
        self.note_havent_slug = Note.objects.create(
            title=TITLE_FIELD,
            text=TEXT_FIELD,
            author=self.author,
        )
        self.assertEqual(
            self.author_client.get(
                reverse(
                    'notes:detail',
                    args=(slugify(self.note_havent_slug.title),))
            ).status_code,
            HTTPStatus.OK)
        self.assertEqual(Note.objects.count(), 2)

    def test_only_one_original_slug(self):
        self.form_data['slug'] = SLUG_FIELD
        self.assertFormError(
            self.author_client.post(reverse('notes:add'), data=self.form_data),
            'form',
            'slug',
            errors=(SLUG_FIELD + WARNING)
        )

    def test_author_can_delete_comment(self):
        self.author_client.delete(
            reverse('notes:delete', args=self.slug_arg)
        )
        self.assertEqual(Note.objects.count(), 0)

    def test_not_author_cant_delete_comment(self):
        self.assertEqual(
            self.not_author_client.delete(
                reverse('notes:delete', args=self.slug_arg)
            ).status_code,
            HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_comment(self):
        self.assertRedirects(
            self.author_client.post(
                reverse(
                    'notes:edit',
                    args=self.slug_arg),
                data=self.form_data
            ),
            reverse('notes:success')
        )
        self.note.refresh_from_db()
        self.assertEqual(
            self.note_attrs,
            self.note_updated_attrs
        )

    def test_not_author_cant_edit_comment(self):
        self.assertEqual(
            self.not_author_client.post(
                reverse(
                    'notes:edit',
                    args=self.slug_arg),
                data=self.form_data
            ).status_code,
            HTTPStatus.NOT_FOUND
        )
        self.note.refresh_from_db()
        self.assertNotEqual(
            self.note_attrs,
            self.note_updated_attrs
        )
