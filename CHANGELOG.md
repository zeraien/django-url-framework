# Changelog

## [Unreleased]
- use of `inflection` library will be the default after 2021

## [0.5.0] - 2020-04-10
### Added
- @auto() decorator, will render your `action` response based on the HTTP Accept header
- @json_action(json_encoder=None) decorator, will render all `action` returns as JSON
- @yaml_action(default_flow_style=None) decorator, will render all `action` returns as YaML
- Site.autodiscover() now accepts `new_inflection_library` parameter, if True, controller names will be translated into URLs using the `inflection` library
- Decorators can now be imported directly from `django_url_framework.decorators`
- `use_inflection_library` for `ActionController`, if set to `None`, allows the `Site` to control it, oterwise the controller can override the `Site` setting.
- `yaml_default_flow_style` - If you want collections to be always serialized in the block style, set to False
- `json_default_encoder` - Set your custom JSONEncoder class
- Return a 2 item tuple from any `action` with the second item being the desired status code.