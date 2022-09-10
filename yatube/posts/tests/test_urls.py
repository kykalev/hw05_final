from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='auth')
        # Создаем группу
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        # Создаем Пост
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        # Чистим кеш перед каждым тестом
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.post.author)

    # Проверяем общедоступные страницы
    def test_public_pages(self):
        templates_url_names = (
            reverse('posts:index'),
            reverse('posts:group_posts', args=(self.group.slug,)),
            reverse('posts:profile', args=(self.post.author,)),
            reverse('posts:post_detail', args=(self.post.id,))
        )
        for url in templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем страницы доступные авторизованному пользователю
    def test_post_create_authorized_client(self):
        response_create = self.authorized_client.get('/create/')
        response_comment = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/'
        )
        self.assertEqual(response_create.status_code, HTTPStatus.OK)
        self.assertEqual(response_comment.status_code, HTTPStatus.FOUND)

    # Проверяем страницы доступные автору
    def test_post_edit_authorized_client(self):
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем запрос к несуществующей странице
    def test_unexisting(self):
        """Несуществующая страница выдаёт код 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
