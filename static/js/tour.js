/**
 * Tour guiado — passo a passo iluminado por tela (driver.js).
 *
 * Cada template define window.CRM_TOUR = { key: 'fila', steps: [...] } e inclui
 * o driver.js (CDN) + este arquivo. O tour roda automaticamente na primeira
 * visita (localStorage tour_<key>) ou quando a URL traz ?tour=1.
 */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        if (!window.CRM_TOUR || !window.driver || !window.driver.js) return;
        var cfg = window.CRM_TOUR;
        var usuario = document.body.dataset.username || '';
        var chave = 'tour_' + cfg.key + '_' + usuario;
        var forcado = new URLSearchParams(window.location.search).get('tour') === '1';
        if (localStorage.getItem(chave) && !forcado) return;

        // mantém só os passos cujo elemento existe na página
        var steps = cfg.steps.filter(function (s) {
            return !s.element || document.querySelector(s.element);
        });
        if (!steps.length) return;

        var d = window.driver.js.driver({
            showProgress: true,
            progressText: '{{current}} de {{total}}',
            nextBtnText: 'Próximo →',
            prevBtnText: '← Anterior',
            doneBtnText: 'Entendi!',
            overlayOpacity: 0.6,
            stagePadding: 6,
            steps: steps,
            onDestroyed: function () {
                localStorage.setItem(chave, '1');
            },
        });
        // pequeno atraso para a página assentar (tabelas, calendário)
        setTimeout(function () { d.drive(); }, 600);
    });
})();
