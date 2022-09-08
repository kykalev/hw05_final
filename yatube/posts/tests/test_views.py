import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post
from posts.forms import PostForm

User = get_user_model()


# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
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
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Создаем Пост
        cls.post = Post.objects.create(
            author=PostTests.user,
            text='Тестовый пост',
            group=PostTests.group,
            image=uploaded,
        )
        # Создаем коммент
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.group_url = (
            'posts:group_posts',
            'group_list.html',
            (cls.group.slug,)
        )
        cls.post_create_url = (
            'posts:post_create',
            'create_post.html',
            None
        )
        cls.post_edit_url = (
            'posts:post_edit',
            'create_post.html',
            (cls.post.id,)
        )
        cls.post_detail_url = (
            'posts:post_detail',
            'post_detail.html',
            (cls.post.id,)
        )
        cls.profile_url = (
            'posts:profile',
            'profile.html',
            (cls.post.author,)
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование,
        # перемещение, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Чистим кеш перед каждым тестом
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostTests.user)

    def check_context_page_or_post(self, context, post=False):
        if post:
            pass
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, PostTests.user)
        self.assertEqual(post.pub_date, PostTests.post.pub_date)
        self.assertEqual(post.text, PostTests.post.text)
        self.assertEqual(post.group, PostTests.post.group)
        self.assertEqual(post.image, PostTests.post.image)

    def test_follow_and_unfollow(self):
        # создаем подписчика
        self.follower = User.objects.create_user(username='follower')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower)
        # количкство подписок до подписки
        count_follow = Follow.objects.count()
        # подписываемся на auth
        self.authorized_client.get(
            reverse('posts:profile_follow', args=(PostTests.post.author,))
        )
        # проверяем добавилась ли подписка
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        # проверяем одинаковое ли количчество постов у автора и фоловера
        posts_count = Post.objects.filter(author=PostTests.post.author).count()
        self.assertEqual(Follow.objects.count(), posts_count)
        count_follow_new = Follow.objects.count()
        # удаляем из подписки
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(PostTests.post.author,))
        )
        self.assertEqual(Follow.objects.count(), count_follow_new - 1)
        # проверяем не одинаковое количчество постов у автора и фоловера
        self.assertNotEqual(Follow.objects.count(), posts_count)

    def test_index_cache_is_ok(self):
        # Создаем пост
        self.post_2 = Post.objects.create(
            author=PostTests.user,
            text='Проверка кэша',
        )
        # запрос к index
        response = self.authorized_client.get(reverse('posts:index'))
        # проверка контекста
        first_object = response.context['page_obj'][0]
        task_text_1 = first_object.text
        task_author_1 = first_object.author.username
        self.assertEqual(task_text_1, 'Проверка кэша')
        self.assertEqual(task_author_1, 'auth')
        # Удаляем последний созданный пост
        Post.objects.filter(pk=self.post_2.pk).delete()
        # Новый запрос к index
        response_new = self.authorized_client.get(reverse('posts:index'))
        # Проверяем что контент не изменился
        self.assertEqual(response.content, response_new.content)
        # очищаем кеш
        cache.clear()
        # Новы запрос к index и сравниваем что контент не эквивалентен
        response_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_clear.content, response_new.content)

    def test_group_posts_context_is_ok(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        url, _, args = PostTests.group_url
        response = self.guest_client.get(reverse(url, args=args))
        self.check_context_page_or_post(context=response.context)
        group = response.context['group']
        self.assertEqual(group.title, PostTests.group.title)

    def test_post_create_and_edit_is_ok(self):
        urls = (
            PostTests.post_create_url,
            PostTests.post_edit_url,
        )
        for name, _, args in urls:
            with self.subTest(name=name):
                is_edit_bool_value = bool(name == 'posts:post_edit')
                response = self.authorized_client.get(reverse(name, args=args))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                self.assertIn('is_edit', response.context)
                is_edit = response.context['is_edit']
                self.assertIsInstance(is_edit, bool)
                self.assertEqual(is_edit, is_edit_bool_value)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь
        templates_urls_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': f'{self.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.post.author}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/create_post.html',
        }
        # Проверяем, при обращении к name вызывается соответствующий шаблон
        for revers_name, url in templates_urls_names.items():
            with self.subTest(revers_name=revers_name):
                response = self.authorized_client.get(revers_name)
                self.assertTemplateUsed(response, url)

    def test_index_context_is_ok(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        task_author_0 = first_object.author.username
        task_group_0 = first_object.group.title
        task_image_0 = first_object.image
        self.assertEqual(task_text_0, 'Тестовый пост')
        self.assertEqual(task_author_0, 'auth')
        self.assertEqual(task_group_0, 'Тестовая группа')
        self.assertEqual(task_image_0, 'posts/small.gif')

    def test_post_detail_context_is_ok(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        url, _, args = PostTests.post_detail_url
        post_count = Post.objects.count()
        comment_count = Comment.objects.count()
        response = self.guest_client.get(reverse(url, args=args))
        response_auth = self.authorized_client.get(reverse(url, args=args))
        self.assertEqual(
            response.context.get('post').author,
            PostTests.post.author)
        self.assertEqual(
            response.context.get('post').image,
            PostTests.post.image)
        self.assertIn('form', response_auth.context)
        self.assertIn('comments', response_auth.context)
        self.assertEqual(post_count, 1)
        self.assertEqual(comment_count, 1)

    def test_profile_context_is_ok(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url, _, args = PostTests.profile_url
        response = self.guest_client.get(reverse(url, args=args))
        self.check_context_page_or_post(context=response.context)
        author = response.context['author']
        self.assertEqual(author, PostTests.post.author)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
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
        # Создаем Посты 13 шт
        cls.posts = [Post(
            author=cls.user,
            text=f'Тестовый пост # {i}',
            group=cls.group
        ) for i in range(1, 14)
        ]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        # Чистим кеш перед каждым тестом
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_index_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_posts_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            args=[PaginatorViewsTest.group.slug]))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_posts_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            args=[PaginatorViewsTest.group.slug]) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            args=[PaginatorViewsTest.user.username]))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.authorized_client.get(reverse(
            'posts:profile',
            args=[PaginatorViewsTest.user.username]) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
