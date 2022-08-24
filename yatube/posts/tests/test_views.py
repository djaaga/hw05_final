from itertools import islice

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsViewTestCase(TestCase):
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
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post(self, post_to_compare: Post):
        self.assertIsInstance(post_to_compare, Post)
        self.assertEqual(post_to_compare.text, self.post.text)
        self.assertEqual(post_to_compare.group, self.post.group)
        self.assertEqual(post_to_compare.author, self.post.author)

    def test_post_creation_additional_check(self):
        views = (
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={
                    'username': f'{PostsViewTestCase.post.author.username}'
                }
            ),
            reverse(
                'posts:group_posts',
                kwargs={'slug': f'{PostsViewTestCase.post.group.slug}'}
            ),
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': PostsViewTestCase.post.id
                }
            ),
        )
        for view in views:
            response = self.authorized_client.get(view)
            with self.subTest(view=view):
                self.assertContains(response, PostsViewTestCase.post.text)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/post_create.html': reverse('posts:post_create'),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'auth'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={
                    'post_id': f'{self.post.pk}'})
            ),
            'posts/group_list.html': (
                reverse('posts:group_posts', kwargs={'slug': 'test-slug'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_posts_gets_posts_of_the_group(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={
                'slug': f'{PostsViewTestCase.group.slug}'}))
        group_posts = response.context['page_obj'].object_list
        for post in group_posts:
            self.assertEqual(post.group.slug, PostsViewTestCase.group.slug)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))

        self.check_post(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )

        self.check_post(response.context['page_obj'].object_list[0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            )
        )
        first_object_list = response.context['page_obj'].object_list[0]
        first_object_list.group.slug = first_object_list.group.slug

        self.check_post(response.context['page_obj'][0])
        self.assertEqual(
            first_object_list.group.slug,
            PostsViewTestCase.group.slug
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': PostsViewTestCase.post.id
                }
            )
        )

        self.check_post(response.context['posts'])

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        reseiving_form = response.context['form']
        self.assertEqual(reseiving_form.instance.text, '')

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        response = self.authorized_client.get(
            reverse(
                'posts:post_edit', kwargs={
                    'post_id': PostsViewTestCase.post.id
                }
            )
        )

        reseiving_form = response.context['form']
        self.assertEqual(reseiving_form.instance.id, PostsViewTestCase.post.id)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug'
        )
        cls.author = User.objects.create_user(username='author')
        cls.posts = []
        batch_size = 10
        objs = (Post(
            text=f'Тестовая запись {i}',
            author=cls.author,
            group=cls.group)for i in range(13))
        while True:
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            Post.objects.bulk_create(batch, batch_size)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_utils_ten_posts(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_PAGINATE
        )

        response = self.authorized_client.get(
            reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}
            )
        )
        self.assertEqual(
            len(response.context['page_obj'].object_list), settings.POSTS_PAGINATE
        )

        response = self.client.get(
            reverse('posts:profile', kwargs={'username': 'author'})

        )
        self.assertEqual(
            len(response.context['page_obj'].object_list), settings.POSTS_PAGINATE)

    def test_second_page_utils_three_posts(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj'].object_list), 3)

        response = self.client.get(
            reverse(
                'posts:group_posts', kwargs={'slug': 'test-slug'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj'].object_list), 3)

        response = self.client.get(
            reverse(
                'posts:profile', kwargs={'username': 'author'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj'].object_list), 3)


class TestPostsPage(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        TestPostsPage.author_client = Client()
        TestPostsPage.author_client.force_login(TestPostsPage.user)

    def test_new_post(self):
        """Новый пост отражается на указанных страницах"""
        urls = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'author'}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = TestPostsPage.author_client.get(url)
                first_object = response.context['page_obj'][0]
                post_author = first_object.author
                post_text = first_object.text
                post_group = first_object.group
                self.assertEqual(post_author, TestPostsPage.post.author)
                self.assertEqual(post_text, TestPostsPage.post.text)
                self.assertEqual(post_group, TestPostsPage.post.group)

    def test_new_post_absence(self):
        TestPostsPage.user_2 = User.objects.create_user(
            username='another_author'
        )
        TestPostsPage.group_2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
        )
        TestPostsPage.post_2 = Post.objects.create(
            author=TestPostsPage.user,
            text='Другой пост',
            group=TestPostsPage.group_2,
        )
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client.get(
            reverse(
                'posts:group_posts', kwargs={
                    'slug': TestPostsPage.group_2.slug
                }
            )
        )
        self.assertNotIn(TestPostsPage.post.text, TestPostsPage.group_2.slug)

        self.author_client.get(
            reverse(
                'posts:profile', kwargs={
                    'username': 'another_author'
                }
            )
        )
