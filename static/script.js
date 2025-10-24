document.addEventListener('DOMContentLoaded', () => {
    const config = {
        apiBaseUrl: '', 
        defaultLang: 'zh',
    };

    const translations = {
        heroTitle: { zh: "AI生成教育动画，自动播放，一键导出视频", en: "AI-generated educational animations with one-click video export" },
        startCreatingTitle: { zh: "开始创作", en: "Start Creating" },
        githubrepo: { zh: "Github 开源仓库", en: "Instructional Animation Github Repo" },
        officialWebsite: { zh: "通向之路社区", en: " Open Source Community" },
        groupChat: { zh: "联系我们/加入交流群", en: "Contact Us" },
        placeholders: {
            zh: ["微积分的几何原理", "冒泡排序","热寂", "黑洞是如何形成的"],
            en: ["What is Heat Death?", "How are black holes formed?", "What is Bubble Sort?"]
        },
        newChat: { zh: "新对话", en: "New Chat" },
        newChatTitle: { zh: "新对话", en: "New Chat" },
        chatPlaceholder: {
            zh: "AI 生成结果具有随机性，您可在此输入修改意见",
            en: "Results are random. Enter your modifications here for adjustments."
        },
        sendTitle: { zh: "发送", en: "Send" },
        agentThinking: { zh: "AI 正在进行思考与规划，请稍后。这可能需要数十秒至数分钟...", en: "AI is thinking and planning, please wait..." },
        generatingCode: { zh: "生成代码中...", en: "Generating code..." },
        codeComplete: { zh: "代码已完成", en: "Code generated" },
        openInNewWindow: { zh: "在新窗口中打开", en: "Open in new window" },
        saveAsHTML: { zh: "保存为 HTML", en: "Save as HTML" },
        exportAsVideo: { zh: "导出为视频", en: "Export as Video" },
        featureComingSoon: { zh: "该功能正在开发中，将在不久的将来推出。\n 请关注我们的官方 GitHub 仓库以获取最新动态！", en: "This feature is under development and will be available soon.\n Follow our official GitHub repository for the latest updates!" },
        visitGitHub: { zh: "访问 GitHub", en: "Visit GitHub" },
        errorMessage: { zh: "抱歉，服务出现了一点问题。请稍后重试。", en: "Sorry, something went wrong. Please try again later." },
        errorFetchFailed: {zh: "LLM服务不可用，请稍后再试", en: "LLM service is unavailable. Please try again later."},
        errorTooManyRequests: {zh: "今天已经使用太多，请明天再试", en: "Too many requests today. Please try again tomorrow."},
        errorLLMParseError: {zh: "返回的动画代码解析失败，请调整提示词重新生成。", en: "Failed to parse the returned animation code. Please adjust your prompt and try again."},
    };

    const suggestionTopics = {
        zh: {
            algorithms: ["冒泡算法", "快速排序", "Dijkstra算法", "贪心算法", "动态规划求解背包问题", "分治算法"],
            physics: ["光的折射", "量子隧穿", "超导现象", "牛顿摆演示动量守恒", "电磁感应", "声波共振"],
            chemistry: ["酸碱中和实验", "化学平衡移动原理", "氧化还原反应", "电解水实验", "滴定分析", "催化剂的作用"],
            mathematics: ["勾股定理", "微积分基本定理", "欧拉公式", "费马小定理", "贝叶斯定理", "斐波那契数列"],
            biology: ["DNA复制过程", "细胞呼吸", "光合作用", "免疫系统反应", "孟德尔遗传规律", "神经元信息传递"]
        },
        en: {
            algorithms: ["Bubble Sort", "Quick Sort basics", "Dijkstra's algorithm", "Greedy algorithms", "Dynamic programming knapsack", "Divide-and-conquer sorting"],
            physics: ["Refraction of light", "Quantum tunneling", "Superconductivity", "Newton's cradle momentum", "Electromagnetic induction", "Sound resonance"],
            chemistry: ["Acid-base neutralization", "Le Chatelier's principle", "Redox reactions", "Electrolysis of water", "Titration curves", "Catalyst in reactions"],
            mathematics: ["Pythagorean theorem", "Fundamental theorem of calculus", "Euler's formula", "Fermat's little theorem", "Bayes' theorem", "Fibonacci sequence"],
            biology: ["DNA replication", "Cellular respiration", "Photosynthesis", "Immune response", "Mendelian inheritance", "Neuron signal transmission"]
        }
    };

    let currentLang = config.defaultLang;
    const body = document.body;
    const initialForm = document.getElementById('initial-form');
    const initialInput = document.getElementById('initial-input');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatLog = document.getElementById('chat-log');
    const newChatButton = document.getElementById('new-chat-button');
    const languageSwitcher = document.getElementById('language-switcher');
    const placeholderContainer = document.getElementById('animated-placeholder');
    const topicSuggestionsContainer = document.getElementById('topic-suggestions');
    const featureModal = document.getElementById('feature-modal');
    const modalGitHubButton = document.getElementById('modal-github-button');
    const modalCloseButton = document.getElementById('modal-close-button');

    const templates = {
        user: document.getElementById('user-message-template'),
        status: document.getElementById('agent-status-template'),
        code: document.getElementById('agent-code-template'),
        player: document.getElementById('animation-player-template'),
        error: document.getElementById('agent-error-template'),
    };

    class LLMParseError extends Error {
        constructor(message, code = 'LLM_UNKNOWN_ERROR') {
            super(message);
            this.name = 'LLMParseError';
            this.code = code;
        }
    }

    let conversationHistory = [];
    let accumulatedCode = '';
    let placeholderInterval;

    function handleFormSubmit(e) {
        e.preventDefault();
        const isInitial = e.currentTarget.id === 'initial-form';
        const submitButton = isInitial
            ? initialForm?.querySelector('button')
            : chatForm?.querySelector('button');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add('disabled');
        }
        const input = isInitial ? initialInput : chatInput;
        const topic = input.value.trim();
        if (!topic) return;

        if (isInitial) switchToChatView();

        conversationHistory.push({ role: 'user', content: topic });
        startGeneration(topic);
        input.value = '';
        if (isInitial) placeholderContainer?.classList?.remove('hidden');
    }

    async function startGeneration(topic) {
        console.log('Getting generation from backend.');
        appendUserMessage(topic);
        const agentThinkingMessage = appendAgentStatus(translations.agentThinking[currentLang]);
        const submitButton = document.querySelector('.submit-button');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add('disabled');
        }
        accumulatedCode = '';
        let inCodeBlock = false;
        let codeBlockElement = null;

        try {
            const response = await fetch(`${config.apiBaseUrl}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: topic, history: conversationHistory })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;

                    const jsonStr = line.substring(6);
                    if (jsonStr.includes('[DONE]')) {
                        console.log('Streaming complete');
                        conversationHistory.push({ role: 'assistant', content: accumulatedCode });

                        if (!codeBlockElement) {
                            console.warn('No code block element created. Full response:', accumulatedCode);
                            throw new LLMParseError('LLM did not return a complete code block.');
                        }

                        if (!isHtmlContentValid(accumulatedCode)) {
                            console.warn('Invalid HTML received:\n', accumulatedCode);
                            throw new LLMParseError('Invalid HTML content received.');
                        }

                        markCodeAsComplete(codeBlockElement);

                        try {
                            if (accumulatedCode) {
                                appendAnimationPlayer(accumulatedCode, topic);
                            }
                        } catch (err) {
                            console.error('appendAnimationPlayer failed:', err);
                            throw new LLMParseError('Animation rendering failed.');
                        }
                        scrollToBottom();
                        return;
                    }

                    let data;
                    try {
                        data = JSON.parse(jsonStr);
                    } catch (err) {
                        console.error('Failed to parse JSON:', jsonStr);
                        throw new LLMParseError('Invalid response format from server.');
                    }

                    if (data.error) {
                        throw new LLMParseError(data.error);
                    }
                    const token = data.token || '';

                    if (!inCodeBlock && token.includes('```')) {
                        inCodeBlock = true;
                        if (agentThinkingMessage) agentThinkingMessage.remove();
                        codeBlockElement = appendCodeBlock();
                        const contentAfterMarker = token.substring(token.indexOf('```') + 3).replace(/^html\n/, '');
                        updateCodeBlock(codeBlockElement, contentAfterMarker);
                    } else if (inCodeBlock) {
                        if (token.includes('```')) {
                            inCodeBlock = false;
                            const contentBeforeMarker = token.substring(0, token.indexOf('```'));
                            updateCodeBlock(codeBlockElement, contentBeforeMarker);
                        } else {
                            updateCodeBlock(codeBlockElement, token);
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Streaming failed:", error);
            if (agentThinkingMessage) agentThinkingMessage.remove();

            if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
                showWarning(translations.errorFetchFailed[currentLang]);
            } else if (error.message.includes('status: 429')) {
                showWarning(translations.errorTooManyRequests[currentLang]);
            } else if (error instanceof LLMParseError) {
                showWarning(translations.errorLLMParseError[currentLang]);
            } else {
                showWarning(translations.errorFetchFailed[currentLang]); // 默认 fallback
            }

            appendErrorMessage(translations.errorMessage[currentLang]);  // 保留 chat-log 中的提示
        } finally {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.classList.remove('disabled');
        }
    }
    }

    function switchToChatView() {
        body.classList.remove('show-initial-view');
        body.classList.add('show-chat-view');
        languageSwitcher.style.display = 'none';
        document.getElementById('logo-chat').style.display = 'block';
    }

    function appendFromTemplate(template, text) {
        const node = template.content.cloneNode(true);
        const element = node.firstElementChild;
        if (text) element.innerHTML = element.innerHTML.replace('${text}', text);
        element.querySelectorAll('[data-translate-key]').forEach(el => {
            const key = el.dataset.translateKey;
            const translation = translations[key]?.[currentLang];
            if (translation) el.textContent = translation;
        });
        chatLog.appendChild(element);
        scrollToBottom();
        return element;
    }

    const appendUserMessage = (text) => appendFromTemplate(templates.user, text);
    const appendAgentStatus = (text) => appendFromTemplate(templates.status, text);
    const appendErrorMessage = (text) => appendFromTemplate(templates.error, text);
    const appendCodeBlock = () => appendFromTemplate(templates.code);

    function updateCodeBlock(codeBlockElement, text) {
        const codeElement = codeBlockElement.querySelector('code');
        if (!text || !codeElement) return;
        const span = document.createElement('span');
        span.textContent = text;
        codeElement.appendChild(span);
        accumulatedCode += text;

        const codeContent = codeElement.closest('.code-content');
        if (codeContent) {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    codeContent.scrollTop = codeContent.scrollHeight;
                });
            });
        }
    }

    function markCodeAsComplete(codeBlockElement) {
        codeBlockElement.querySelector('[data-translate-key="generatingCode"]').textContent = translations.codeComplete[currentLang];
        codeBlockElement.querySelector('.code-details').removeAttribute('open');
    }

    function appendAnimationPlayer(htmlContent, topic) {
        console.log('Appending animation player with topic:', topic);
        const node = templates.player.content.cloneNode(true);
        const playerElement = node.firstElementChild;
        playerElement.querySelectorAll('[data-translate-key]').forEach(el => {
            const key = el.dataset.translateKey;
            el.textContent = translations[key]?.[currentLang] || el.textContent;
        });
        const iframe = playerElement.querySelector('.animation-iframe');
        iframe.srcdoc = htmlContent;

        playerElement.querySelector('.open-new-window').addEventListener('click', () => {
            const content = iframe?.srcdoc || htmlContent || '';
            const blob = new Blob([content], { type: 'text/html' });
            window.open(URL.createObjectURL(blob), '_blank');
        });
        playerElement.querySelector('.save-html').addEventListener('click', () => {
            const content = iframe?.srcdoc || htmlContent || '';
            const blob = new Blob([content], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = Object.assign(document.createElement('a'), { href: url, download: `${topic.replace(/\s/g, '_') || 'animation'}.html` });
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(url);
            a.remove();
        });
        playerElement.querySelector('.export-video')?.addEventListener('click', async (ev) => {
            const btn = ev.currentTarget;
            let timerId = null;
            let elapsed = 0;
            const originalText = btn.querySelector('span')?.textContent || '导出为视频';
            const progressBar = document.createElement('div');
            progressBar.style.cssText = 'position:absolute;left:0;bottom:0;height:3px;width:0;background:#4a90e2;transition:width 0.3s;';
            btn.disabled = true;
            btn.classList.add('disabled');
            btn.style.position = 'relative';
            btn.querySelector('span').textContent = '处理中... 0s';
            btn.appendChild(progressBar);

            const tick = () => {
                elapsed += 1;
                btn.querySelector('span').textContent = `处理中... ${elapsed}s`;
                const pct = Math.min(95, Math.floor((elapsed / 30) * 95)); // 预估进度条，最多到95%
                progressBar.style.width = pct + '%';
            };
            timerId = setInterval(tick, 1000);

            try {
                const htmlText = iframe?.srcdoc || htmlContent || '';
                const resp = await fetch('/record', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        html_text: htmlText,
                        width: 1280,
                        height: 720,
                        fps: 24,
                        wait_until: 'networkidle',
                        timeout: 180000,
                        end_event: 'recording:finished',
                        end_timeout: 180000,
                        mp4: true,
                        headless: true,
                    })
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.error || `HTTP ${resp.status}`);
                }
                const data = await resp.json();
                const mp4Url = data.mp4_url || '';
                if (!mp4Url) {
                    throw new Error('未获取到 MP4 下载地址，请检查服务端 FFmpeg 是否已安装并成功转码。');
                }
                const cacheBustedMp4Url = `${mp4Url}?t=${Date.now()}`;
                progressBar.style.width = '100%';
                btn.querySelector('span').textContent = '完成，开始下载';
                const a = document.createElement('a');
                a.href = cacheBustedMp4Url;
                try {
                    const u = new URL(mp4Url, window.location.origin);
                    const name = u.pathname.split('/').pop() || 'animation.mp4';
                    a.download = name;
                } catch (_) {
                    a.download = 'animation.mp4';
                }
                document.body.appendChild(a);
                a.click();
                a.remove();

                // 仅在生成 MP4 成功时，展示内联在线播放预览
                if (mp4Url) {
                    const container = playerElement.querySelector('.player-container');
                    let preview = playerElement.querySelector('.exported-video-preview');
                    if (!preview) {
                        preview = document.createElement('div');
                        preview.className = 'exported-video-preview';
                        preview.style.cssText = 'margin-top:12px;padding:12px;border-radius:12px;background:#f7f9fc;border:1px solid #e6edf5;';
                        const title = document.createElement('div');
                        title.textContent = '导出视频预览（MP4）';
                        title.style.cssText = 'font-size:14px;color:#445;opacity:0.9;margin-bottom:8px;';
                        const video = document.createElement('video');
                        video.setAttribute('controls', '');
                        video.setAttribute('preload', 'metadata');
                        video.style.width = '100%';
                        video.style.maxHeight = '480px';
                        video.style.borderRadius = '8px';
                        video.src = cacheBustedMp4Url;
                        preview.appendChild(title);
                        preview.appendChild(video);
                        container.appendChild(preview);
                    } else {
                        const video = preview.querySelector('video');
                        if (video) video.src = cacheBustedMp4Url;
                    }
                }
            } catch (e) {
                console.error('导出视频失败:', e);
                showWarning((e && e.message) || '导出视频失败');
            } finally {
                clearInterval(timerId);
                setTimeout(() => {
                    btn.disabled = false;
                    btn.classList.remove('disabled');
                    btn.querySelector('span').textContent = originalText;
                    progressBar.remove();
                }, 1500);
            }
        });
        chatLog.appendChild(playerElement);
        scrollToBottom();
    }

    function isHtmlContentValid(htmlContent) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlContent, "text/html");

        // 检查是否存在解析错误
        const parseErrors = doc.querySelectorAll("parsererror");
        if (parseErrors.length > 0) {
            console.warn("HTML 解析失败：", parseErrors[0].textContent);
            return false;
        }

        // 可选：检测是否有 <html><body> 结构或是否为空
        if (!doc.body || doc.body.innerHTML.trim() === "") {
            console.warn("HTML 内容为空");
            return false;
        }

        return true;
    }

    const scrollToBottom = () => chatLog.scrollTo({ top: chatLog.scrollHeight, behavior: 'smooth' });

    function setNextPlaceholder() {
        const placeholderTexts = translations.placeholders[currentLang];
        const newSpan = document.createElement('span');
        newSpan.textContent = placeholderTexts[placeholderIndex];
        placeholderContainer.innerHTML = '';
        placeholderContainer.appendChild(newSpan);
        placeholderIndex = (placeholderIndex + 1) % placeholderTexts.length;
    }

    function startPlaceholderAnimation() {
        if (placeholderInterval) clearInterval(placeholderInterval);
        const placeholderTexts = translations.placeholders[currentLang];
        if (placeholderTexts && placeholderTexts.length > 0) {
            placeholderIndex = 0;
            setNextPlaceholder();
            placeholderInterval = setInterval(setNextPlaceholder, 4000);
        }
    }

    function pickRandomTopics(desiredCount = 6) {
        const topicsByLang = suggestionTopics[currentLang] || {};
        const categoryLists = Object.values(topicsByLang).filter(list => Array.isArray(list) && list.length > 0);
        if (categoryLists.length === 0) return [];
        const allTopics = categoryLists.flat();
        let count = Math.random() < 0.5 ? 5 : 6;
        count = Math.min(count, desiredCount, allTopics.length);
        const selected = [];
        const used = new Set();

        categoryLists.forEach(list => {
            if (selected.length >= count) return;
            const available = list.filter(item => !used.has(item));
            if (available.length === 0) return;
            const candidate = available[Math.floor(Math.random() * available.length)];
            used.add(candidate);
            selected.push(candidate);
        });

        const remaining = allTopics.filter(item => !used.has(item));
        while (selected.length < count && remaining.length > 0) {
            const index = Math.floor(Math.random() * remaining.length);
            const [topic] = remaining.splice(index, 1);
            used.add(topic);
            selected.push(topic);
        }

        return selected.slice(0, count);
    }

    function renderTopicSuggestions() {
        if (!topicSuggestionsContainer) return;
        topicSuggestionsContainer.innerHTML = '';
        const topics = pickRandomTopics(6);
        if (topics.length === 0) {
            topicSuggestionsContainer.style.display = 'none';
            return;
        }
        topicSuggestionsContainer.style.display = 'flex';
        topics.forEach(topic => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'topic-suggestion';
            button.textContent = topic;
            button.addEventListener('click', () => {
                initialInput.value = topic;
                if (placeholderContainer) {
                    placeholderContainer.classList.add('hidden');
                }
                initialInput.focus();
                initialInput.dispatchEvent(new Event('input', { bubbles: true }));
            });
            topicSuggestionsContainer.appendChild(button);
        });
    }

    function setLanguage(lang) {
        if (!['zh', 'en'].includes(lang)) return;
        currentLang = lang;
        document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
        document.querySelectorAll('[data-translate-key]').forEach(el => {
            const key = el.dataset.translateKey;
            const translation = translations[key]?.[lang];
            if (!translation) return;
            if (el.hasAttribute('placeholder')) el.placeholder = translation;
            else if (el.hasAttribute('title')) el.title = translation;
            else el.textContent = translation;
        });
        languageSwitcher.querySelectorAll('button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });
        startPlaceholderAnimation();
        renderTopicSuggestions();
        localStorage.setItem('preferredLanguage', lang);
    }

    let placeholderIndex = 0;

    function init() {
        initialInput.addEventListener('input', () => {
            placeholderContainer.classList.toggle('hidden', initialInput.value.length > 0);
        });
        initialInput.addEventListener('focus', () => {
            clearInterval(placeholderInterval);
            renderTopicSuggestions();
        });
        initialInput.addEventListener('blur', () => {
            if (initialInput.value.length === 0) startPlaceholderAnimation();
        });

        initialForm.addEventListener('submit', handleFormSubmit);
        chatForm.addEventListener('submit', handleFormSubmit);
        newChatButton.addEventListener('click', () => location.reload());
        languageSwitcher.addEventListener('click', (e) => {
            const target = e.target.closest('button');
            if (target) setLanguage(target.dataset.lang);
        });

        function hideModal() {
            featureModal.classList.remove('visible');
        }

        modalCloseButton.addEventListener('click', hideModal);
        featureModal.addEventListener('click', (e) => {
            if (e.target === featureModal) hideModal();
        });

        modalGitHubButton.addEventListener('click', () => {
            window.open('https://github.com/yourusername/ai-animation', '_blank');
            hideModal();
        });

        const savedLang = localStorage.getItem('preferredLanguage');
        const browserLang = navigator.language?.toLowerCase() || ''; // e.g. 'zh-cn'

        let initialLang = 'en'; 
        if (['zh', 'en'].includes(savedLang)) {
            initialLang = savedLang;
        } else if (browserLang.startsWith('zh')) {
            initialLang = 'zh';
        } else if (browserLang.startsWith('en')) {
            initialLang = 'en';
        }

        setLanguage(initialLang);
    }

    init();
});

function showWarning(message) {
    const box = document.getElementById('warning-box');
    const overlay = document.getElementById('overlay');
    const text = document.getElementById('warning-message');
    text.textContent = message;
    box.style.display = 'flex';
    overlay.style.display = 'block';

    setTimeout(() => {
        hideWarning();
    }, 10000);
}

function hideWarning() {
    document.getElementById('warning-box').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}
