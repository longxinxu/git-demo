const syncBtn = document.getElementById('sync-btn');

if (syncBtn) {
  syncBtn.addEventListener('click', async () => {
    syncBtn.disabled = true;
    syncBtn.textContent = '同步中...';
    try {
      await fetch('/trigger-sync', { method: 'POST' });
      window.location.reload();
    } catch (error) {
      syncBtn.disabled = false;
      syncBtn.textContent = '同步失败，请重试';
    }
  });
}
