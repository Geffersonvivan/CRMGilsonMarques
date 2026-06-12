/**
 * Onboarding — banners de primeira visita e toasts de aprendizado.
 *
 * Banner: <div class="onb-banner" data-onboarding="chave"> ... </div>
 *   Aparece só até o usuário fechar (estado em localStorage onb_<chave>).
 * Toast: showLearnToast('mensagem') — aviso flutuante de 5s.
 */
(function () {
    'use strict';

    // ===== Banners de primeira visita =====
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-onboarding]').forEach(function (el) {
            var usuario = document.body.dataset.username || '';
            var chave = 'onb_' + el.dataset.onboarding + '_' + usuario;
            if (localStorage.getItem(chave)) return;
            el.classList.add('onb-visible');
            var btn = document.createElement('button');
            btn.className = 'onb-close';
            btn.type = 'button';
            btn.innerHTML = '&times;';
            btn.title = 'Entendi, não mostrar de novo';
            btn.addEventListener('click', function () {
                localStorage.setItem(chave, '1');
                el.classList.remove('onb-visible');
            });
            el.appendChild(btn);
        });
    });

    // ===== Toast de aprendizado =====
    window.showLearnToast = function (msg) {
        var t = document.createElement('div');
        t.className = 'learn-toast';
        t.innerHTML = msg;
        document.body.appendChild(t);
        requestAnimationFrame(function () { t.classList.add('show'); });
        setTimeout(function () {
            t.classList.remove('show');
            setTimeout(function () { t.remove(); }, 400);
        }, 5200);
    };
})();
