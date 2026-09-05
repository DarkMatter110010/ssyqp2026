// 鸡汤
const JTS = [
    '生命在于运动！',
    '运动是健康的源泉，也是长寿的秘诀。',
    '人的健全，不但靠饮食，还靠运动。',
    '更快、更高、更强。',
    '活动有方，五脏自和。',
    '当我的双腿开始移动的时候，我的思维开始涌流。',
    '身体是革命的本钱！',
    '奔跑益生，益起向前。',
    '益起跑，益起改变世界。',
    '一步一善，奔向未来。',
    '心怀善意，脚步不停。',
    '益起行动，益起奔跑，为爱加速！',
    '用脚步丈量爱心，用行动改变世界。',
    '每一步都是爱的传递，每一程都是善的积累。',
    '跑出健康，跑出公益，跑向更好的未来。',
    '益起跑，不止是速度，更是态度。',
    '让爱与希望随着每一公里延伸。',
    '你跑，我跑，大家益起跑。',
    '每一步，都是为世界贡献一份力量。',
    '益起跑，为爱而动，为善而行。',
    '跑步中积累健康，公益中积累善意。',
    '益起跑，用行动证明爱与责任。',
    '跑动生命，为爱发声。',
    '益起跑，公益心，健康行。',
    '健康与善意，跑出来的每一步都是丰收。',
    '从心出发，跑出健康，跑出善意。',
    '益起跑，益起前进，益起改变。',
    '每一公里都是爱的表达，每一步都是善的象征。',
    '益起跑，益起传递温暖和希望。',
    '益起跑，一路为爱加速。',
    '一双跑鞋，一份爱心，改变世界的每一步。',
    '益起跑，益起行动，益起助力美好未来。',
    '每一步都是向更美好未来的迈进。',
    '益起跑，汇聚每一份爱的力量。',
    '用脚步传递爱，用速度传递希望。',
    '益起跑，益起共赢未来。',
    '跑在公益路上，爱在你我心中。',
    '跑步益健康，爱心益世界。',
    '益起跑，益起传递爱与正能量。',
    '跑步益健康，公益益世界。',
    '每一步都在改变自己，也在改变世界。',
    '益起跑，汇聚点滴善行，改变万千世界。',
    '跑步是一种力量，公益是一种信仰。',
    '益起跑，用健康和爱心铺就未来的路。',
    '益起跑，携手并肩，向爱出发。',
    '每一个脚印，都留下爱的足迹。',
    '益起跑，用双脚丈量善意的距离。',
    '跑步益身心，公益益人间。',
    '健康与爱心同行，奔跑与善意共存。',
    '益起跑，益起行动，益起创造美好。',
    '跑向更健康的你，跑向更美好的世界。',
    '益起跑，益起助力更美好的明天。',
    '每一步，都在奔向更好的自己和世界。',
    '益起跑，用脚步传递善与爱。',
    '奔跑中传递温暖，公益中创造美好。',
    '益起跑，益起拼搏，为爱前行。',
    '跑步益心，公益益情，一路携手同行。'
];

// 年级代号 → 显示名称
const GRADE_NAMES = {
    '1': 'D', '2': 'E', '3': 'F',
    '4': 'DAP', '5': 'EAP', '6': 'FAP'
};

const { createApp, ref, computed, onMounted, onBeforeUnmount } = Vue;

// ================= 数据请求层 =================
const REQUEST_INTERVAL = 5000;   // 里程数据轮询间隔（毫秒）
const QUOTE_INTERVAL = 30000;    // 格言更换间隔（毫秒）
const ANIM_MS = 1200;            // 总里程数字滚动动画时长（毫秒）

/** POST 请求并解析 JSON */
async function postJSON(url) {
    const res = await fetch(url, { method: 'POST' });
    return res.json();
}

/**
 * 一次并发拉取总里程与班级排行。
 * 返回 { total, classes }，对应接口失败时该字段为 null。
 */
async function fetchMileage() {
    const [sum, list] = await Promise.allSettled([
        postJSON('/api/sum'),
        postJSON('/api/list')
    ]);
    return {
        total: sum.status === 'fulfilled' && sum.value && sum.value.status === 'ok'
            ? sum.value.sum_distance : null,
        classes: list.status === 'fulfilled' && list.value && list.value.status === 'ok'
            ? list.value.data : null
    };
}

// ================= 页面组件 =================
createApp({
    setup() {
        // 响应式数据源：请求只需更新这两个变量，模板全部由 Vue 自动绑定
        const displayTotal = ref(0);
        const classes = ref([]);
        const quote = ref('无');

        // 展示值由 Vue 自动推导，数据一变即自动重渲染
        const totalText = computed(() =>
            Number(displayTotal.value).toLocaleString()
        );
        // 里程降序（里程相同时按班级代号升序）
        const sortedClasses = computed(() =>
            [...classes.value].sort((a, b) =>
                (b.distance - a.distance) || (a.class_code.localeCompare(b.class_code))
            )
        );

        function formatClass(code) {
            const grade = GRADE_NAMES[String(code)[0]] || '班级';
            const num = parseInt(String(code).substring(1), 10);
            return grade + num;
        }

        function formatDistance(m) {
            const value = Number(m) || 0;
            if (value >= 10000) {
                return (value / 1000).toFixed(1) + ' km';
            }
            return value.toLocaleString() + ' m';
        }

        // 总里程数字滚动动画（新一轮开始时取消上一轮，避免动画叠加跳动）
        let countAnimId = null;
        function countUp(target) {
            const start = displayTotal.value;
            const diff = Number(target) - start;
            if (diff === 0) return;
            if (countAnimId !== null) cancelAnimationFrame(countAnimId);
            const t0 = performance.now();
            const step = (now) => {
                const p = Math.min(1, (now - t0) / ANIM_MS);
                displayTotal.value = Math.floor(start + diff * p);
                countAnimId = p < 1 ? requestAnimationFrame(step) : null;
            };
            countAnimId = requestAnimationFrame(step);
        }

        // 刷新里程数据：失败静默，等待下一轮轮询
        async function refresh() {
            try {
                const { total, classes: list } = await fetchMileage();
                if (total !== null) countUp(total);
                if (list !== null) classes.value = list;
            } catch (e) { /* 网络错误等：静默，等下一轮 */ }
        }

        // 随机格言
        function upQuote() {
            quote.value = JTS[Math.floor(Math.random() * JTS.length)];
        }

        // 生命周期自动启动/停止轮询，页面销毁后不再残留定时器
        let quoteTimer = null;
        let pollTimer = null;
        onMounted(() => {
            upQuote();
            refresh();
            quoteTimer = setInterval(upQuote, QUOTE_INTERVAL);
            pollTimer = setInterval(refresh, REQUEST_INTERVAL);
        });
        onBeforeUnmount(() => {
            clearInterval(quoteTimer);
            clearInterval(pollTimer);
        });

        // 模板只依赖这些导出值（computed 在模板中自动解包）
        return {
            quote,
            totalText,
            sortedClasses,
            formatClass,
            formatDistance
        };
    }
}).mount('#app');
