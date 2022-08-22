from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_authorized_client_exist(self):
        """Доступность страниц для авторизированного пользователя."""
        urls_for_authorized_client = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/auth/': 200,
            f'/posts/{self.post.pk}/': 200,
            '/create/': 302,
            '/unexisting_page/': 404,
        }

        for adress, code in urls_for_authorized_client.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.pk}/edit/': 'posts/post_create.html',
        }

        for url, template in templates_url_names.items():
            with self.subTest(url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    # Проверяем редиректы для неавторизованного пользователя
    def test_url_author_exists_at_desired_location(self):
        """Страница доступна только автору"""
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/edit/',
        )

    def test_url_for_guest_users(self):
        """"Тестирование доступности страниц для гостей."""
        urls_for_all_users = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/auth/': 200,
            f'/posts/{self.post.pk}/': 200,
            '/create/': 302,
            '/unexisting_page/': 404,
        }

        for adress, code in urls_for_all_users.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_task_list_url_exists_at_desired_location(self):
        """Несуществующая страница возвращает ошибку 404."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
