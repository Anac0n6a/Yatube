import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class TestView(TestCase):
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
            text='Тестовый текст для поста',
            group=cls.group,
        )

        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый текст для комментария',
            post=cls.post
        )

        cls.templates_name = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug':
                    cls.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                    cls.user}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                    cls.post.pk}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id':
                    cls.post.pk}): 'posts/post_create.html',
        }

    def setUp(self):
        self.user_auntificated = Client()
        self.user_auntificated.force_login(self.user)
        self.quest_user = Client()

    def test_template_is_ok(self):
        '''проверка соответсивю шаблонов для view функций'''
        for reverse_name, templates in self.templates_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.user_auntificated.get(reverse_name)
                self.assertTemplateUsed(response, templates)

    def test_index_corrected_context(self):
        '''Проверка на то, соответствует ли шаблон index контексту'''
        response = self.user_auntificated.get(reverse('posts:index'))
        expected = list(Post.objects.all().order_by('-pub_date'))[:10]
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_group_list_corrected_context(self):
        '''Проверка на то, соответствует ли шаблон group_list контексту'''
        response = (self.user_auntificated.get(reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})))
        expected = list(Post.objects.filter(group_id=self.group.id)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_profile_corrected_context(self):
        '''Проверка на то, соответствует ли шаблон profile контексту'''
        response = self.user_auntificated.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        expected = list(Post.objects.filter(author_id=self.user.id)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_post_detail_corrected_context(self):
        '''Проверка на то, соответствует ли шаблон post_detail контексту'''
        response = self.user_auntificated.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post_obj').text, self.post.text)
        self.assertEqual(response.context.get('post_obj').author,
                         self.post.author)
        self.assertEqual(response.context.get('post_obj').group,
                         self.post.group)

    def test_post_create_edit_corrected_context(self):
        '''Проверка на то, соответствует ли шаблон post_create контексту'''
        response = self.user_auntificated.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context['form'].fields[value]
                self.assertIsInstance(form, expected)

    def test_post_create_corrected_context(self):
        '''Проверка на то, соответствует ли шаблон post_create контексту'''
        response = self.user_auntificated.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context['form'].fields[value]
                self.assertIsInstance(form, expected)

    def test_сreating_a_post_is_shown_in_the_right_pages(self):
        '''Проверка что при создании поста, он отоброжается на страницах'''
        form_fields = {
            reverse('posts:index'): Post.objects.get(group=self.post.group),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse('posts:profile', kwargs={
                'username': self.user}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.user_auntificated.get(value)
                form = response.context['page_obj']
                self.assertIn(expected, form)

    def test_post_not_added_alien_group(self):
        '''Проверка что пост не попал в чужую группу'''
        form_fields = {
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group)
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.user_auntificated.get(value)
                form = response.context['page_obj']
                self.assertNotIn(expected, form)

    def test_comment_corected_work(self):
        '''Проверка что комментарий создает запись и
         доступен только авторизированным пользователям'''
        comments_count = Comment.objects.count()
        text = {'text': 'Тестовый текст для комментария'}
        response = self.user_auntificated.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=text
        )
        response_quest = self.quest_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=text
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response_quest.status_code, 302)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Тестовый текст для комментария').exists())

    def test_cahce_corrected(self):
        response = self.quest_user.get('posts:index')
        result1 = response.content
        Post.objects.get(id=1).delete()
        response2 = self.quest_user.get('posts:index')
        result2 = response2.content
        self.assertEqual(result1, result2)

    def test_templates_404(self):
        '''Проверка что страница 404 отдает кастомный шаблон'''
        response = self.quest_user.get('/about/dsfsdj')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_follow_auth_user_is_corrected(self):
        '''Проверка авторизованный пользователь
        может подписываться на других и удалять их из подписок'''
        follow_count = Follow.objects.count()
        # Стр изранных пустая
        r_0 = self.user_auntificated.get(reverse('posts:follow_index'))
        self.assertEqual(len(r_0.context['page_obj']), 0)
        # Подписка
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response = self.user_auntificated.get(
            reverse('posts:follow_index')
        )
        # Проверка обработки подписки
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        # Проверка что избранное не показывается у другого пользователя
        user23 = User.objects.create(username="BezImeni")
        self.user_auntificated.force_login(user23)
        r_2 = self.user_auntificated.get(reverse("posts:follow_index"))
        self.assertNotIn(self.post, r_2.context["page_obj"])
        self.assertEqual(len(response.context['page_obj']), 1)
        # Отписка
        Follow.objects.all().delete()
        response2 = self.user_auntificated.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response2.context['page_obj']), 0)
        self.assertEqual(Follow.objects.count(), follow_count)
        # Проврка что гостя перенаправляет на стр авторизации
        response3 = self.quest_user.get(reverse('posts:follow_index'))
        self.assertEqual(response3.status_code, 302)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImagePagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ImagePagesTest, cls).setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_group_slug',
            description='Test group description',
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.quest_client = Client()

    def test_image_and_context_for_pages(self):
        '''Изображение передается на страницы через context'''
        templates = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        )
        for url in templates:
            with self.subTest(url):
                response = self.quest_client.get(url)
                obj = response.context['page_obj'][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_and_context_for_post_detaul(self):
        '''Проверка Изображение передается на страницы
         через context в post_detail'''
        response = self.quest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        obj = response.context['post_obj']
        self.assertEqual(obj.image, self.post.image)

    def test_image_create_in_db(self):
        '''Проверка, передана ли картинка в Базу Данных при создании поста'''
        self.assertTrue(
            Post.objects.filter(text='Тестовый текст',
                                image='posts/small.gif').exists()
        )
