/* Client-only daily report image export. Vendored dependencies load on demand. */
(() => {
  'use strict';
  const source = document.querySelector('main');
  const date = source?.querySelector('header time[datetime]')?.getAttribute('datetime');
  if (!source || !/^\d{4}-\d{2}-\d{2}$/.test(date || '')) return;
  const assetRoot = new URL('.', document.currentScript.src);
  const reportURL = `https://yaoshining.github.io/github-insights/reports/${date.replaceAll('-', '/')}.html`;
  const filename = `GitHub-Insights-${date}.png`;
  const tools = document.createElement('div');
  tools.className = 'share-tools';
  tools.innerHTML = '<button type="button" class="share-button">生成分享长图</button><span class="share-hint">含网站标题与当期二维码</span>';
  source.querySelector('header').after(tools);
  const trigger = tools.querySelector('button');
  const dialog = document.createElement('dialog');
  dialog.className = 'share-dialog';
  dialog.setAttribute('aria-labelledby', 'share-title');
  dialog.innerHTML = `<div class="share-dialog-head"><h2 id="share-title">分享 GitHub 日报</h2><button type="button" class="share-close" aria-label="关闭分享预览">关闭</button></div>
    <p class="share-status" role="status" aria-live="polite"></p>
    <div class="share-preview" hidden><img alt="GitHub Insights 完整日报分享长图，含网站标题和当期二维码"></div>
    <div class="share-actions"><a class="share-button" data-save hidden>保存图片</a><button type="button" class="share-button" data-share hidden>分享图片</button><button type="button" class="share-button" data-retry hidden>重新生成</button></div>
    <p class="share-hint">图片在本机生成。保存后可转发到社交软件；手机也可长按预览图保存。二维码可打开当期完整日报。</p>`;
  document.body.append(dialog);
  const status = dialog.querySelector('[role="status"]');
  const preview = dialog.querySelector('.share-preview');
  const img = preview.querySelector('img');
  const save = dialog.querySelector('[data-save]');
  const share = dialog.querySelector('[data-share]');
  const retry = dialog.querySelector('[data-retry]');
  const loads = new Map();
  let objectURL, file, busy = false;
  function load(name) {
    if (!loads.has(name)) {
      const promise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        const fail = () => { clearTimeout(timer); script.remove(); reject(new Error('加载图片组件失败，请检查网络后重试。')); };
        const timer = setTimeout(fail, 20000);
        script.src = new URL(`vendor/${name}`, assetRoot).href;
        script.onload = () => { clearTimeout(timer); resolve(); };
        script.onerror = fail;
        document.head.append(script);
      }).catch(error => { loads.delete(name); throw error; });
      loads.set(name, promise);
    }
    return loads.get(name);
  }
  function qrCanvas() {
    const code = window.qrcode(0, 'M');
    code.addData(reportURL, 'Byte');
    code.make();
    const cells = code.getModuleCount(), cell = 6, quiet = 4;
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = (cells + quiet * 2) * cell;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#000';
    for (let r = 0; r < cells; r++) for (let c = 0; c < cells; c++) {
      if (code.isDark(r, c)) ctx.fillRect((c + quiet) * cell, (r + quiet) * cell, cell, cell);
    }
    return canvas;
  }
  async function generate() {
    if (busy) return;
    busy = true; trigger.disabled = true;
    retry.hidden = save.hidden = share.hidden = preview.hidden = true;
    status.textContent = '正在生成完整长图，请稍候…';
    let capture;
    try {
      await Promise.all([load('html2canvas-1.4.1.js'), load('qrcode-generator-1.4.4.js')]);
      await document.fonts.ready;
      capture = source.cloneNode(true);
      capture.className = 'container share-capture';
      capture.setAttribute('aria-hidden', 'true');
      capture.querySelectorAll('nav,.share-tools,script').forEach(el => el.remove());
      [capture, ...capture.querySelectorAll('[id]')].forEach(el => el.removeAttribute('id'));
      capture.style.cssText = 'position:absolute;left:-10000px;top:0;pointer-events:none;';
      const brand = document.createElement('div');
      brand.className = 'share-brand';
      brand.innerHTML = '<div><div class="share-brand-title">GitHub Insights</div><p class="share-brand-subtitle">每日追踪开源动态 · 热门项目精选</p></div><div class="share-qr"><p>扫码阅读当期日报</p></div>';
      brand.querySelector('.share-qr').prepend(qrCanvas());
      capture.prepend(brand);
      const urlLine = document.createElement('p'); urlLine.textContent = reportURL;
      capture.querySelector('footer').append(urlLine);
      document.body.append(capture);
      const height = capture.scrollHeight;
      // Bound memory and canvas dimensions on mobile while retaining the entire report.
      const scale = Math.min(1.5, Math.sqrt(4500000 / (720 * height)), 16000 / height);
      const canvas = await window.html2canvas(capture, {
        backgroundColor: '#16213e', scale, logging: false,
        windowWidth: 1000, windowHeight: 1000, scrollX: 0, scrollY: 0,
      });
      const blob = await new Promise((resolve, reject) => canvas.toBlob(value => value ? resolve(value) : reject(new Error('图片生成失败，请重试。')), 'image/png'));
      file = new File([blob], filename, { type: 'image/png' });
      if (objectURL) URL.revokeObjectURL(objectURL);
      objectURL = URL.createObjectURL(blob);
      img.src = objectURL; save.href = objectURL; save.download = filename;
      preview.hidden = save.hidden = false;
      share.hidden = !(navigator.share && navigator.canShare?.({ files: [file] }));
      status.textContent = '长图已生成，可向下滚动检查完整内容。';
    } catch (error) {
      status.textContent = error.message || '生成失败，请重试。';
      retry.hidden = false;
    } finally {
      capture?.remove(); busy = false; trigger.disabled = false;
    }
  }
  trigger.addEventListener('click', () => { dialog.showModal(); generate(); });
  retry.addEventListener('click', generate);
  dialog.querySelector('.share-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); dialog.close(); }
  });
  dialog.addEventListener('close', () => trigger.focus());
  share.addEventListener('click', async () => {
    try {
      await navigator.share({ files: [file], title: `GitHub Insights · ${date}` });
    } catch (error) {
      if (error.name !== 'AbortError') status.textContent = '系统分享暂不可用，请保存图片后转发。';
    }
  });
})();
