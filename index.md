---
layout: default
title: Audit Dashboard
---

# BYDT Audit Dashboard

This dashboard shows key metrics from the governed self-improving system audit logs.

## Executive Decision Report

[Open the Executive Decision Report](docs/executive-report.html)

Plain-language GREEN/YELLOW/RED decision signals, closure guidance, and evidence links for AGE governance rows.

<div id="dashboard">
  <p>Loading dashboard data...</p>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  async function loadDashboard() {
    try {
      const response = await fetch('docs/dashboard-data.json');
      const data = await response.json();

      const container = document.getElementById('dashboard');
      container.innerHTML = `
        <div style="display: flex; gap: 20px; margin: 30px 0;">
          <div style="background: #fff; padding: 20px; border-radius: 8px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div>Total Audits</div>
            <div style="font-size: 2rem; font-weight: bold; color: #BFA16B;">${data.total_audits}</div>
          </div>
          <div style="background: #fff; padding: 20px; border-radius: 8px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div>Refusals</div>
            <div style="font-size: 2rem; font-weight: bold; color: #BFA16B;">${data.refusals}</div>
          </div>
          <div style="background: #fff; padding: 20px; border-radius: 8px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div>Refusal Rate</div>
            <div style="font-size: 2rem; font-weight: bold; color: #BFA16B;">${data.refusal_rate}%</div>
          </div>
        </div>

        <h2>Top Refusal Reasons</h2>
        <canvas id="reasons-chart" width="400" height="200"></canvas>
      `;

      // Render chart
      const ctx = document.getElementById('reasons-chart');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.top_reasons.map(r => r.reason),
          datasets: [{
            label: 'Count',
            data: data.top_reasons.map(r => r.count),
            backgroundColor: '#BFA16B'
          }]
        },
        options: {
          responsive: true,
          scales: { y: { beginAtZero: true } }
        }
      });
    } catch (error) {
      document.getElementById('dashboard').innerHTML = '<p>Failed to load dashboard data.</p>';
      console.error(error);
    }
  }

  loadDashboard();
</script>
