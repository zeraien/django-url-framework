import unittest
from os.path import dirname

from django.conf import settings
settings.configure(
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.dummy.TemplateStrings',
            'APP_DIRS': False,
            'DIRS': [dirname(__file__)]
        },
    ]

)

if __name__ == '__main__':
    unittest.main()
