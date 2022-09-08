from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cache.clear()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        if settings.DEBUG:
            pass
        else:
            templates_url_names = {
                '/unexisting_page/': 'core/404.html',
            }
            for url, template in templates_url_names.items():
                with self.subTest(url=url):
                    response = URLTests.authorized_client.get(url)
                    self.assertTemplateUsed(response, template)
