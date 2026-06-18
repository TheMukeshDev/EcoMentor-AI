export function dashboardSkeleton() {
  return `
    <div class="dashboard-skeleton">
      <div class="skeleton-hero"></div>
      <div class="skeleton-grid">
        ${Array(4).fill('<div class="skeleton-grid-item"></div>').join('')}
      </div>
      <div class="skeleton-section"></div>
      <div class="skeleton-grid">
        ${Array(3).fill('<div class="skeleton-grid-item"></div>').join('')}
      </div>
      <div class="skeleton-section"></div>
      <div class="skeleton-section"></div>
    </div>
  `;
}

export function leaderboardSkeleton() {
  return `
    <div class="leaderboard-page">
      <div class="skeleton" style="width:200px;height:32px;border-radius:8px;margin-bottom:24px"></div>
      <div class="skeleton-card">
        ${Array(5).fill(`
          <div style="display:flex;align-items:center;gap:12px;padding:8px 0">
            <div class="skeleton" style="width:28px;height:28px;border-radius:50%;flex-shrink:0"></div>
            <div class="skeleton-line" style="flex:1"></div>
            <div class="skeleton" style="width:60px;height:24px;border-radius:12px"></div>
            <div class="skeleton" style="width:50px;height:20px;border-radius:4px"></div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

export function achievementsSkeleton() {
  return `
    <div class="achievements-page">
      <div class="skeleton" style="width:200px;height:32px;border-radius:8px;margin-bottom:8px"></div>
      <div class="skeleton" style="width:300px;height:20px;border-radius:4px;margin-bottom:24px"></div>
      <div class="skeleton-card" style="text-align:center;padding:32px">
        <div class="skeleton" style="width:80px;height:80px;border-radius:50%;margin:0 auto 12px"></div>
        <div class="skeleton" style="width:180px;height:28px;border-radius:8px;margin:0 auto 8px"></div>
        <div class="skeleton" style="width:100px;height:16px;border-radius:4px;margin:0 auto 16px"></div>
        <div class="skeleton" style="width:300px;height:8px;border-radius:4px;margin:0 auto"></div>
      </div>
      <div class="badges-grid">
        ${Array(4).fill(`
          <div class="skeleton-card" style="text-align:center">
            <div class="skeleton" style="width:40px;height:40px;border-radius:50%;margin:0 auto 8px"></div>
            <div class="skeleton" style="width:80px;height:16px;border-radius:4px;margin:0 auto 4px"></div>
            <div class="skeleton" style="width:60px;height:12px;border-radius:4px;margin:0 auto"></div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
