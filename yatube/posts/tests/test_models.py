from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class Test(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='тестовое Название группы',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        str_list = (
            (str(self.post), self.post.text[:15]),
            (str(self.group), self.group.title),
        )
        for value, expected in str_list:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for value, expeted in field_verboses.items():
            with self.subTest(value=value):
                (self.assertEqual(self.post._meta.get_field(
                    value).verbose_name,
                 expeted))

    def test_help_text(self):
        '''help_text в полях совпадает с ожидаемым.'''
        field_help = {
            'text': 'Введите текст поста',
            'group': 'Группа к которой будет относиться пост'
        }
        for value, expected in field_help.items():
            with self.subTest(value=value):
                (self.assertEqual(self.post._meta.get_field(value).help_text,
                 expected))
