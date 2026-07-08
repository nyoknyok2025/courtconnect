from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginCaptchaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='captchatest',
            password='StrongPass123!',
        )

    def test_login_page_shows_captcha_checkbox(self):
        response = self.client.get(reverse('charlie_app:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "I'm not a robot")

    def test_login_requires_captcha_checkbox(self):
        response = self.client.post(
            reverse('charlie_app:login'),
            {
                'username': self.user.username,
                'password': 'StrongPass123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
