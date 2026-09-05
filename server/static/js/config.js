const { createApp } = Vue;

const SALT = 'b7c85d29-8b56-468e-9c17-f85eddb75bc9';

async function sha256Hex(text) {
    const data = new TextEncoder().encode(text);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(digest))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
}

createApp({
    data() {
        return {
            classCode: '',
            distance: '',
            password: '',
            activeKeypad: '',   // '' | 'class' | 'distance'
            statusText: '',
            statusClass: '',    // 'ok' | 'error'
            submitting: false,
            _closeTimer: null
        };
    },
    watch: {
        // 仅允许数字输入，并限制长度
        classCode(v) {
            this.classCode = v.replace(/\D/g, '').slice(0, 3);
        },
        distance(v) {
            this.distance = v.replace(/\D/g, '').slice(0, 7);
        }
    },
    methods: {
        /* ---- 小键盘 ---- */
        openKeypad(field) {
            clearTimeout(this._closeTimer);
            this.activeKeypad = field;
        },
        scheduleClose(field) {
            clearTimeout(this._closeTimer);
            this._closeTimer = setTimeout(() => {
                if (this.activeKeypad === field) this.activeKeypad = '';
            }, 150);
        },
        closeKeypad() {
            clearTimeout(this._closeTimer);
            this.activeKeypad = '';
        },
        _targetField() {
            return this.activeKeypad === 'class' ? 'classCode' : 'distance';
        },
        keypadPress(d) {
            const field = this._targetField();
            const maxLen = this.activeKeypad === 'class' ? 3 : 7;
            if (this[field].length >= maxLen) return;
            this[field] = this[field] + d;
            this.statusText = '';
            this.statusClass = '';
        },
        keypadBack() {
            const field = this._targetField();
            this[field] = this[field].slice(0, -1);
        },
        keypadClear() {
            const field = this._targetField();
            this[field] = '';
        },

        /* ---- 里程滚轮步进（400 米倍数） ---- */
        onWheel(e) {
            const cur = this.distance === '' ? 0 : parseInt(this.distance, 10) || 0;
            let next;
            if (e.deltaY < 0) {
                // 向上滚动：比当前值大且最近的 400 的倍数
                next = Math.ceil((cur + 1) / 400) * 400;
            } else {
                // 向下滚动：比当前值小且最近的 400 的倍数，最小为 0
                next = Math.floor((cur - 1) / 400) * 400;
                if (next < 0) next = 0;
            }
            this.distance = String(next);
        },

        /* ---- 状态展示 ---- */
        setStatus(ok, msg) {
            this.statusText = msg;
            this.statusClass = ok ? 'ok' : 'error';
        },

        /* ---- 提交 ---- */
        async submit() {
            if (this.submitting) return;
            this.statusText = '';
            this.statusClass = '';

            if (!this.classCode) {
                this.setStatus(false, '班级代号不能为空');
                return;
            }
            if (!this.password) {
                this.setStatus(false, '密码不能为空');
                return;
            }

            // 里程为空按 0 处理；须为 0~9999999 的整数（不超过 7 位）
            const dist = this.distance === '' ? 0 : parseInt(this.distance, 10);
            if (Number.isNaN(dist) || dist < 0 || dist > 9999999) {
                this.setStatus(false, '里程需为 0~9999999 的整数');
                return;
            }

            this.submitting = true;
            try {
                // 密码使用 Web Crypto API 加密（SHA-256(密码 + 盐)），后端仅接收密文
                const pwHash = await sha256Hex(this.password + SALT);
                const res = await fetch('/api/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        class_code: this.classCode,
                        distance: dist,
                        password: pwHash
                    })
                });
                const data = await res.json();
                if (data.status === 'ok') {
                    this.setStatus(true, '提交成功');
                    // 班级代号与里程清空，密码保留（密码仅在刷新时清空）
                    this.classCode = '';
                    this.distance = '';
                } else {
                    this.setStatus(false, data.message || '提交失败');
                }
            } catch (err) {
                this.setStatus(false, '网络错误，请稍后重试');
            } finally {
                this.submitting = false;
            }
        }
    }
}).mount('#app');
