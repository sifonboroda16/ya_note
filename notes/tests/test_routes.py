from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


from notes.models import Note

User = get_user_model()
LOGIN_URL = 'users:login'


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author_user')
        cls.not_author = User.objects.create(username='NotAuthor_user')
        cls.note = Note.objects.create(
            title='title',
            text='text',
            slug='slug',
            author=cls.author
        )

        cls.slug_arg = (cls.note.slug,)

    def test_pages_availability(self):
        for url_name in (
            'notes:home',
            LOGIN_URL,
            'users:logout',
            'users:signup',
        ):
            self.assertEqual(self.client.get(
                reverse(url_name)).status_code,
                HTTPStatus.OK)

    def test_only_author_can_detail_edit_delete(self):
        for user, expected_status in (
            (self.author, HTTPStatus.OK),
            (self.not_author, HTTPStatus.NOT_FOUND)
        ):
            self.client.force_login(user)
            for url_name in (
                'notes:edit',
                'notes:delete',
                'notes:detail',
            ):
                with self.subTest(user=user, url_name=url_name):
                    self.assertEqual(
                        self.client.get(reverse(
                            url_name, args=self.slug_arg)).status_code,
                        expected_status)

    def test_redirect_for_anonymous(self):
        for url_name, args in (
            ('notes:add', None),
            ('notes:edit', self.slug_arg),
            ('notes:delete', self.slug_arg),
            ('notes:detail', self.slug_arg),
            ('notes:list', None),
            ('notes:success', None),
        ):
            with self.subTest(url_name):
                self.assertRedirects(
                    self.client.get(reverse(url_name, args=args)),
                    f'{reverse(LOGIN_URL)}'
                    f'?next={reverse(url_name, args=args)}')
