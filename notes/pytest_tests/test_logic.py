import pytest

from pytils.translit import slugify
from http import HTTPStatus

from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertFormError

from notes.forms import WARNING
from notes.models import Note


def test_user_can_create_note(
        author_client,
        author,
        form_data
):
    assertRedirects(
        author_client.post(reverse('notes:add'), data=form_data),
        reverse('notes:success')
    )
    assert Note.objects.count() == 1
    new_note = Note.objects.get()
    assert (
        new_note.title,
        new_note.text,
        new_note.slug,
        new_note.author
    ) == (
        form_data['title'],
        form_data['text'],
        form_data['slug'],
        author
    )


@pytest.mark.django_db
def test_anonymous_user_cant_create_note(client, form_data):
    url = reverse('notes:add')
    assertRedirects(
        client.post(url, data=form_data),
        f'{reverse("users:login")}?next={url}'
    )
    assert Note.objects.count() == 0


def test_unique_slug(author_client, note, form_data):
    form_data['slug'] = note.slug
    assertFormError(
        author_client.post(reverse('notes:add'), data=form_data),
        'form',
        'slug',
        errors=(note.slug + WARNING)
    )
    assert Note.objects.count() == 1


def test_slugify(author_client, form_data):
    form_data.pop('slug')
    assertRedirects(
        author_client.post(reverse('notes:add'), data=form_data),
        reverse('notes:success')
    )
    assert Note.objects.count() == 1
    assert Note.objects.get().slug == slugify(form_data['title'])


def test_other_user_cant_edit_note(not_author_client, form_data, note):
    assert (
        not_author_client.post(
            reverse('notes:edit', args=(note.slug,)),
            data=form_data
        ).status_code == HTTPStatus.NOT_FOUND
    )
    note_from_db = Note.objects.get(id=note.id)
    assert (
        note.title,
        note.text,
        note.slug,
    ) == (
        note_from_db.title,
        note_from_db.text,
        note_from_db.slug,
    )


def test_author_can_delete_note(author_client, slug_for_args):
    assertRedirects(
        author_client.post(reverse('notes:delete', args=slug_for_args)),
        reverse('notes:success'))
    assert Note.objects.count() == 0


def test_other_user_cant_delete_note(not_author_client, slug_for_args):
    assert (
        not_author_client.post(
            reverse('notes:delete', args=slug_for_args)
        ).status_code == HTTPStatus.NOT_FOUND)
    assert Note.objects.count() == 1
