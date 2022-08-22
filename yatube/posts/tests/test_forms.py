from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test-user')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='text',
            author=cls.user,
        )
        cls.form = PostFormTests()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.authorised_user = Client()
        self.authorised_user.force_login(self.user)

    def test_create_post(self):
        """Валидация и создание новой записи Post"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'text',
            'group': self.group.pk,
        }
        response = self.authorised_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={
                    'username': f'{PostFormTests.user}'
                }
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_post(self):
        form_data = {
            'text': 'Отредактированный пост',
            'group': PostFormTests.group.pk,
        }
        response = self.authorised_user.post(
            reverse('posts:post_edit', args=[PostFormTests.post.id]),
            data=form_data,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[PostFormTests.post.id]))

        self.assertTrue(
            PostFormTests.post.text,
            'Отредактированный пост'
        )

    def test_post_comment(self):
        """Валидная форма создаёт комментарий к посту."""
        form_data = {
            'text': 'Тестовый комментарий'
        }
        # Отправляем POST-запрос
        response = self.authorised_user.post(
            reverse('posts:add_comment', kwargs={
                    'post_id': self.post.id
                    }),
            data=form_data,
            follow=True
        )
        # Проверяем редирект на страницу поста
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.id
        }))
        # Проверяем, что комментарий успешно создался
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий'
            ).exists()
        )

    def test_cache_work_is_correct(self):
        """Проверка кеширования на работоспособность."""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
        )
        response = self.authorised_user.get(reverse('posts:index'))
        response_with_post = response.content

        post.delete()

        response = self.authorised_user.get(reverse('posts:index'))
        response_without_post_but_with_cache = response.content
        self.assertEqual(
            response_with_post, response_without_post_but_with_cache,
            'Кеш работает неправильно')

        cache.clear()

        response = self.authorised_user.get(reverse('posts:index'))
        response_without_post_and_cache = response.content
        self.assertNotEqual(
            response_with_post, response_without_post_and_cache,
            'Кеш работает неправильно без постов')


class FollowFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user,
        )

    def setUp(self):
        self.authorised_user = Client()
        self.authorised_user.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_authorised_user_can_subscribe(self):
        """Проверка подписок на пользователя"""
        follows_count = Follow.objects.count()
        self.author_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_a_new_user_record_appears_in_the_subscribers(self):
        ''' В подписчиках появляется новая запись пользователя'''
        response = self.authorised_user.get(
            reverse(
                'posts:follow_index',
            )
        )
        self.assertContains(response, self.post)
