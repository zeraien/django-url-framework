from django.conf import settings
import hashlib
from django.utils.safestring import mark_safe

class FlashMessage(object):
    def __init__(self, message, is_error=False, kind='normal'):
        self.message = message.encode('utf8')
        self.is_error = is_error
        self.kind = kind
    
    def hash(self):
        msgdigest = hashlib.md5(self.message).hexdigest()
        kinddigest = hashlib.md5(self.message).hexdigest()
        return hashlib.md5(msgdigest+kinddigest).hexdigest()

    def json_ready(self):
        return {
            'message': self.message,
            'is_error': self.is_error,
            'kind': self.kind
        }

    def __repr__(self):
        return mark_safe(self.message)

    def __str__(self):
        return mark_safe(self.message)

class FlashManager(object):
    SESSION_KEY = getattr(settings, 'URL_FRAMEWORK_SESSION_KEY', 'django_url_framework_flash')
    def __init__(self, request):
        self.request = request
        self._messages_cache = None
    
    def _get_messages(self):
        if self._messages_cache is None:
            self._messages_cache = []
            if self.SESSION_KEY in self.request.session:
                for msg_data in self.request.session[self.SESSION_KEY]:
                    self._messages_cache.append(FlashMessage(**msg_data))

        return self._messages_cache
    messages = property(_get_messages)
    
    def has_messages(self):
        return len(self) > 0
    
    def clear(self):
        if self.SESSION_KEY in self.request.session:
            del(self.request.session[self.SESSION_KEY])
            self.request.session.save()

    def get_and_clear(self):
        messages = self.messages
        self.clear()
        return messages

    def __nonzero__(self):
        return len(self.messages) > 0

    def __iter__(self):
        return iter(self.messages)

    def __len__(self):
        return len(self.messages)

    def __getitem__(self, key):
        return self.messages[key]
    
    def append_error(self, msg):
        self.append(msg=msg, msg_type='error')
        
    def append(self, msg, msg_type='normal'):

        new_message = FlashMessage(**{'message': msg, 'kind': msg_type, 'is_error': msg_type == 'error'})
        new_hash = new_message.hash()

        for message in self.messages:
            if message.hash() == new_hash:
                return

        self.messages.append(new_message)
        self.request.session[self.SESSION_KEY] = [m.json_ready() for m in self.messages]

    def set(self, msg, msg_type='normal'):
        self.clear()
        self.append(msg=msg, msg_type=msg_type)

    def error(self, msg):
        self.clear()
        self.append(msg=msg, msg_type='error')
