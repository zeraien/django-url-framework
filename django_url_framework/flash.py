from django.conf import settings
import hashlib

class FlashMessage(object):
    def __init__(self,message, is_error = False, kind = 'normal'):
        self.message = message.encode('utf8')
        self.is_error = is_error
        self.kind = kind
    
    def hash(self):
        return hashlib.sha1(u"%s|%s" % (self.message, self.kind)).hexdigest()
    
    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message

class FlashManager(object):
    SESSION_KEY = getattr(settings, 'URL_FRAMEWORK_SESSION_KEY', 'django_url_framework_flash')
    def __init__(self, request):
        self.request = request
        self._messages_cache = None
    
    def _get_messages(self):
        if self._messages_cache is None:
            if self.SESSION_KEY in self.request.session:
                self._messages_cache = self.request.session[self.SESSION_KEY]
            else:
                self._messages_cache = []
        return self._messages_cache
    messages = property(_get_messages)
    
    def has_messages(self):
        return len(self)>0
    
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
        self.append(msg, 'error')
        
    def append(self, msg, msg_type = 'normal'):
        self.messages.append( FlashMessage( **{'message':msg, 'kind': msg_type, 'is_error':msg_type=='error'}) )
        self.request.session[self.SESSION_KEY] = self.messages
    def set(self, msg, msg_type = 'normal'):
        self.append(msg, msg_type)
    def error(self, msg):
        self.append(msg, 'error')
    append_error = error