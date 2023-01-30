from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class TestForms(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_author')
        self.user_auntificated = Client()
        self.user_auntificated.force_login(self.user)

    def test_added_valid_form_post_create(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {"text": "Тестовый текст"}
        response = self.user_auntificated.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse("posts:profile", kwargs={
                "username": self.user.username
            })
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text="Тестовый текст").exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_added_valid_form_post_edit(self):
        '''Валидная форма меняет запись в БД'''
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )

        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст для поста',
            group=self.group,
        )
        post_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': {self.group.id}
        }
        response = self.user_auntificated.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={
                "post_id": self.post.id
            })
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.post.refresh_from_db()
        self.assertTrue(Post.objects.filter(text='Измененный текст').exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
