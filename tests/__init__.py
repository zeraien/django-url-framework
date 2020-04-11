import unittest
from os.path import dirname, join

from django.conf import settings
settings.configure(
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.dummy.TemplateStrings',
            'APP_DIRS': False,
            'DIRS': [join(dirname(__file__),'templates')]
        },
    ]

)

if __name__ == '__main__':
    unittest.main()
