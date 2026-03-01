from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
import uuid

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Auto-generate username
        if not user.username:
            base = data.get("email", "").split("@")[0]
            user.username = slugify(base) + "-" + uuid.uuid4().hex[:6]

        return user
