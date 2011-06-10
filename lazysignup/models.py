import re
from django.conf import settings
from django.db import models

from lazysignup.decorators import USER_AGENT_BLACKLIST
from lazysignup.exceptions import NotLazyError
from lazysignup.utils import is_lazy_user

DEFAULT_BLACKLIST = (
    'slurp',
    'googlebot',
    'yandex',
    'msnbot',
    'baiduspider',
)

for user_agent in getattr(settings, 'LAZYSIGNUP_USER_AGENT_BLACKLIST',
    DEFAULT_BLACKLIST):
    USER_AGENT_BLACKLIST.append(re.compile(user_agent, re.I))


class LazyUserManager(models.Manager):

    def create_lazy_user(self, username):
        """ Create a lazy user.
        """
        user_class = LazyUser.get_user_class()
        user = user_class.objects.create_user(username, '')
        self.create(user=user)
        return user

    def convert(self, form):
        """ Convert a lazy user to a non-lazy one. The form passed
        in is expected to be a ModelForm instance, bound to the user
        to be converted.

        The converted ``User`` object is returned.

        Raises a TypeError if the user is not lazy.
        """
        if not is_lazy_user(form.instance):
            raise NotLazyError('You cannot convert a non-lazy user')

        user = form.save()

        # We need to remove the LazyUser instance assocated with the
        # newly-converted user
        self.filter(user=user).delete()
        return user


class LazyUser(models.Model):
    user = models.ForeignKey(
        getattr(settings, 'LAZYSIGNUP_USER_MODEL', 'auth.User'),
        unique=True)
    objects = LazyUserManager()

    @classmethod
    def get_user_class(cls):
        return cls._meta.get_field('user').rel.to
