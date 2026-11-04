from django.test import RequestFactory, TestCase, override_settings
from django.template.loader import render_to_string


class BaseTemplateTests(TestCase):
    def test_homepage_displays_centered_hero_and_navigation(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1 id="home-title">Modo Finanças</h1>', html=True)
        self.assertContains(response, '<h2>O seu melhor investimento</h2>', html=True)
        self.assertContains(response, 'aria-label="Navegação principal"')
        self.assertContains(response, 'aria-controls="main-navigation"')
        self.assertContains(response, 'Como funciona')
        self.assertContains(response, 'src="/static/finance/imgs/fm_logo_base.png"')
        self.assertContains(response, 'href="/static/finance/css/site.css"')
        self.assertContains(response, 'src="/static/finance/js/navigation.js"')
        self.assertNotContains(response, '<style>')
        self.assertNotContains(response, '<script>\n')

    @override_settings(
        BOOTSTRAP_CSS_URL='http://assets.local/bootstrap.min.css',
        BOOTSTRAP_JS_URL='http://assets.local/bootstrap.bundle.min.js',
    )
    def test_base_template_uses_view_title_and_configured_bootstrap_urls(self):
        html = render_to_string(
            '_base.html',
            {'title': 'Resumo mensal'},
            request=RequestFactory().get('/'),
        )

        self.assertIn('<title>FinanceMode | Resumo mensal</title>', html)
        self.assertIn('href="http://assets.local/bootstrap.min.css"', html)
        self.assertIn('src="http://assets.local/bootstrap.bundle.min.js"', html)
        self.assertIn('lang="pt-BR"', html)
        self.assertIn('FinanceMode', html)

    @override_settings(BOOTSTRAP_CSS_URL='', BOOTSTRAP_JS_URL='')
    def test_base_template_renders_without_bootstrap_urls(self):
        html = render_to_string(
            '_base.html',
            {'title': 'Início'},
            request=RequestFactory().get('/'),
        )

        self.assertIn('<title>FinanceMode | Início</title>', html)
        self.assertIn('href="/static/finance/css/site.css"', html)
        self.assertIn('src="/static/finance/js/navigation.js"', html)
        self.assertNotIn('assets.local', html)
