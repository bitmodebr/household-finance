from django.conf import settings


def bootstrap_assets(request):
    return {
        'bootstrap_css_url': settings.BOOTSTRAP_CSS_URL,
        'bootstrap_js_url': settings.BOOTSTRAP_JS_URL,
    }
