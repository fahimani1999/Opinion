from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class RegisterPageTests(TestCase):
    def test_register_page_renders(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)


class CreatePostPageTests(TestCase):
    def test_create_post_page_renders_for_logged_in_user(self):
        user = get_user_model().objects.create_user(
            username='author',
            password='test-password-123',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('create_post'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'post_form.html')
        self.assertContains(response, '<h1>Create Post</h1>', html=True)
