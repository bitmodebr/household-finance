const navToggle = document.querySelector('.nav-toggle');
const navigation = document.querySelector('#main-navigation');

if (navToggle && navigation) {
    navToggle.addEventListener('click', () => {
        const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
        navToggle.setAttribute('aria-expanded', String(!isExpanded));
        navToggle.setAttribute('aria-label', isExpanded ? 'Abrir menu' : 'Fechar menu');
        navigation.classList.toggle('is-open', !isExpanded);
        document.body.classList.toggle('menu-open', !isExpanded);
    });

    navigation.addEventListener('click', (event) => {
        if (event.target.closest('a')) {
            navToggle.setAttribute('aria-expanded', 'false');
            navToggle.setAttribute('aria-label', 'Abrir menu');
            navigation.classList.remove('is-open');
            document.body.classList.remove('menu-open');
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && navigation.classList.contains('is-open')) {
            navToggle.setAttribute('aria-expanded', 'false');
            navToggle.setAttribute('aria-label', 'Abrir menu');
            navigation.classList.remove('is-open');
            document.body.classList.remove('menu-open');
            navToggle.focus();
        }
    });
}
