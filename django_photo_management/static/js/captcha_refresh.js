/**
 * 点击验证码图片换一张（django-simple-captcha /captcha/refresh/）
 */
(function () {
    function refreshCaptcha(img) {
        var form = img.closest('form');
        if (!form) {
            return;
        }
        fetch('/captcha/refresh/', {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin',
        })
            .then(function (r) {
                if (!r.ok) {
                    throw new Error('refresh failed');
                }
                return r.json();
            })
            .then(function (data) {
                if (!data || !data.key || !data.image_url) {
                    return;
                }
                img.src = data.image_url;
                var hidden = form.querySelector('input[name="captcha_0"]');
                if (hidden) {
                    hidden.value = data.key;
                }
                var answer = form.querySelector('input[name="captcha_1"]');
                if (answer) {
                    answer.value = '';
                    answer.focus();
                }
            })
            .catch(function () {});
    }

    function decorateImages() {
        document.querySelectorAll('img.captcha').forEach(function (img) {
            img.style.cursor = 'pointer';
            if (!img.title) {
                img.title = '看不清？点击图片换一张';
            }
        });
    }

    document.addEventListener('click', function (e) {
        var t = e.target;
        if (t && t.matches && t.matches('img.captcha')) {
            e.preventDefault();
            refreshCaptcha(t);
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', decorateImages);
    } else {
        decorateImages();
    }
})();
