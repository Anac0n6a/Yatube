from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста'
        )

        cls.link_list = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user}/',
            f'/posts/{cls.post.pk}/',
        ]
        cls.templates_url_name = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/follow/': 'posts/follow.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.new_user = User.objects.create(username='new_test_user')
        self.new_client = Client()
        self.new_client.force_login(self.new_user)

    def test_page_displayed(self):
        '''Проверка на открываение страниц для всех пользователей'''
        for address in self.link_list:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_display_for_follow(self):
        '''Проверка что стр подписок не открываются для гостей'''
        url_list = [
            '/follow/',
            f'/profile/{self.user}/follow/',
            f'/profile/{self.user}/unfollow/',
        ]
        for address in url_list:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit_available_only_author(self):
        '''Проверка что страница редактирования, достпна только автору поста'''
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        quest = self.guest_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(quest.status_code, HTTPStatus.FOUND)
        no_author = self.new_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(no_author.status_code, HTTPStatus.FOUND)

    def test_post_create_redirect(self):
        '''Проверка что страница создания поста, делает редирект на
           авторизацию для не авторизирвоанного пользователя'''
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_not_found(self):
        '''Проверка что ненайденная страница возвращает 404'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_templates(self):
        '''URL использует корректный шаблон'''
        for address, templates in self.templates_url_name.items():
            with self.subTest(templates=templates):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, templates)
