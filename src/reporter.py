import json

def generate_report(stats, skipped_count=0, output_path='report.html'):

    traffic_labels = list(stats['traffic_by_hour'].keys())
    def fmt_hour(h):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(h)
            return dt.strftime("%H:00")
        except:
            return h

    def fmt_date(ts):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(ts)
            return dt.strftime("%B %d, %Y")
        except:
            return ts

    traffic_labels_short = [fmt_hour(l) for l in traffic_labels]
    traffic_values = list(stats['traffic_by_hour'].values())
    use_line = len(traffic_values) > 24

    def filter_traffic_data(labels, values):
        if len(labels) <= 12:
            return labels, values
        filtered_labels, filtered_values = [], []
        for i in range(len(labels)):
            if i == 0 or i == len(labels) - 1 or i % 4 == 0:
                filtered_labels.append(labels[i])
                filtered_values.append(values[i])
        return filtered_labels, filtered_values

    traffic_labels_filtered, traffic_values_filtered = filter_traffic_data(traffic_labels_short, traffic_values)

    sd = stats['status_distribution']
    status_label_map = {
        '2xx': 'Success ',
        '4xx': 'Client Error ',
        '5xx': 'Server Error ',
        'other': 'Other'
    }
    pie_labels, pie_values, pie_colors = [], [], []
    color_map = {
        '2xx':   '#16a34a',
        '4xx':   '#f59e0b',
        '5xx':   '#ef4444',
        'other': '#6b7280',
    }
    for bucket in ['2xx', '4xx', '5xx', 'other']:
        t = sum(sd.get(bucket, {}).values())
        if t:
            pie_labels.append(status_label_map[bucket])
            pie_values.append(t)
            pie_colors.append(color_map[bucket])

    rt = stats['response_time_buckets']
    rt_labels = list(rt.keys())
    rt_values = list(rt.values())

    top_ep = stats['top_endpoints']
    slow_ep = stats['slowest_endpoints']
    top_ips = stats['top_ips']
    failed  = stats['failed_logins_by_ip']
    total   = stats['total']

    time_start = stats['time_range']['start'] if stats.get('time_range') else 'N/A'
    time_end   = stats['time_range']['end']   if stats.get('time_range') else 'N/A'
    date_start = fmt_date(time_start)
    date_end   = fmt_date(time_end)

    def error_rate():
        errors = sum(sd.get('4xx', {}).values()) + sum(sd.get('5xx', {}).values())
        return f"{errors/total*100:.1f}%" if total else "0%"

    def avg_response():
        all_avgs = [v for _, v in slow_ep]
        return f"{sum(all_avgs)/len(all_avgs):.0f}" if all_avgs else "N/A"

    def top_ep_rows():
        rows = ""
        for i, (ep, cnt) in enumerate(top_ep):
            pct = cnt/total*100
            rows += f"""<
                <td class="rank">{i+1}</td>
                <td class="mono">{ep}</td>
                <td class="mono">{cnt:,}</td>
                <td><div class="bar-wrap"><div class="bar-fill" style="width:{pct:.1f}%"></div></div></td>
                <td class="mono muted">{pct:.1f}%</td>
             </tr>"""
        return rows

    def slow_ep_rows():
        rows = ""
        for i, (ep, avg) in enumerate(slow_ep):
            rows += f"""<
                <td class="rank">{i+1}</td>
                <td class="mono">{ep}</td>
                <td class="mono {'danger' if avg > 1000 else 'warn' if avg > 500 else 'success'}">{avg:.0f} ms</td>
             </tr>"""
        return rows

    def ip_rows():
        rows = ""
        for ip, cnt in top_ips:
            rows += f"<tr><td class='mono'>{ip}</td><td class='mono'>{cnt:,}</td><td class='mono muted'>{cnt/total*100:.1f}%</td></tr>"
        return rows

    def failed_rows():
        if not failed:
            return "<tr><td colspan='2' class='muted' style='text-align:center;padding:20px'>No failed logins detected</td></tr>"
        rows = ""
        for ip, cnt in failed:
            rows += f"<tr><td class='mono'>{ip}</td><td class='mono danger'>{cnt:,}</td></tr>"
        return rows

    def status_detail_rows():
        rows = ""
        for bucket, color in [('2xx','success'), ('4xx','warn'), ('5xx','danger')]:
            for code, cnt in sorted(sd.get(bucket, {}).items()):
                label = {
                    200:'OK', 201:'Created', 204:'No Content',
                    400:'Bad Request', 401:'Unauthorized', 403:'Forbidden',
                    404:'Not Found', 429:'Too Many Requests',
                    500:'Internal Server Error', 502:'Bad Gateway', 503:'Service Unavailable'
                }.get(int(code), '')
                rows += f"<tr><td class='mono {color}'>{code}</td><td>{label}</td><td class='mono'>{cnt:,}</td><td class='mono muted'>{cnt/total*100:.1f}%</td></tr>"
        return rows

    chart_type = 'line' if use_line else 'bar'
    line_extra = """
      tension: 0.3,
      fill: true,
      pointRadius: 3,
      pointBackgroundColor: '#f97316',
    """ if use_line else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Log Analysis Report</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',sans-serif; background:#f1f5f9; color:#1e293b; }}

  .topbar {{
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    padding: 28px 48px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .topbar-left h1 {{
    font-size: 1.5rem; font-weight: 700; color: #fff; letter-spacing: -0.4px;
  }}
  .topbar-left .subtitle {{
    font-size: 0.82rem; color: #94a3b8; margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
  }}
  .topbar-right {{
    text-align: right;
  }}
  .topbar-right .date-range {{
    font-size: 0.85rem; color: #cbd5e1;
    font-family: 'JetBrains Mono', monospace;
  }}
  .topbar-right .total-badge {{
    display: inline-block; margin-top: 6px;
    background: #1d4ed8; color: #fff;
    font-size: 0.78rem; font-weight: 600;
    padding: 4px 12px; border-radius: 20px;
  }}

  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  .section {{ margin-bottom: 36px; }}
  .section-header {{
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 2px; color: #64748b; margin-bottom: 14px;
    padding-bottom: 8px; border-bottom: 2px solid #e2e8f0;
  }}

  .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; }}
  .card-title {{
    font-size: 0.78rem; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 18px;
  }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .chart-wrap {{ position: relative; height: 300px; }}
  .chart-wrap-tall {{ position: relative; height: 320px; }}

  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.8px; color: #94a3b8; padding: 8px 12px;
    text-align: left; border-bottom: 1px solid #f1f5f9;
  }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f8fafc; font-size: 0.84rem; color: #334155; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f8fafc; }}

  .mono {{ font-family: 'JetBrains Mono', monospace; font-size: 0.79rem; }}
  .muted {{ color: #94a3b8; }}
  .danger {{ color: #ef4444; }}
  .warn {{ color: #f59e0b; }}
  .success {{ color: #16a34a; }}
  .rank {{ color: #cbd5e1; font-weight: 600; width: 28px; }}

  .bar-wrap {{ background: #f1f5f9; border-radius: 4px; height: 6px; width: 100px; }}
  .bar-fill  {{ background: #3b82f6; border-radius: 4px; height: 6px; }}

  .stat-big {{
    display: flex; flex-direction: column; justify-content: center;
    align-items: center; gap: 32px; height: 100%; padding: 16px 0;
  }}
  .stat-big-item {{ text-align: center; }}
  .stat-big-label {{
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.2px; color: #94a3b8; margin-bottom: 10px;
  }}
  .stat-big-value {{
    font-size: 3rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace; line-height: 1;
  }}
  .stat-big-sub {{ font-size: 0.82rem; color: #94a3b8; margin-top: 8px; }}
  .divider {{ width: 60%; height: 1px; background: #f1f5f9; }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <h1>Log Analysis Report</h1>
    <div class="subtitle">Server access log analysis</div>
  </div>
  <div class="topbar-right">
    <div class="date-range">{date_start} &nbsp;&mdash;&nbsp; {date_end}</div>
    <span class="total-badge">{total:,} requests</span>
  </div>
</div>

<div class="container">

  <div class="section">
    <div class="section-header">Traffic</div>
    <div class="card">
      <div class="card-title">Requests Per Hour</div>
      <div class="chart-wrap-tall"><canvas id="trafficChart"></canvas></div>
    </div>
  </div>

  <div class="section">
    <div class="section-header">Status Codes</div>
    <div class="two-col">
      <div class="card">
        <div class="card-title">Distribution</div>
        <div class="chart-wrap"><canvas id="statusChart"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Breakdown</div>
        <table>
          <tr><th>Code</th><th>Description</th><th>Count</th><th>%</th></tr>
          {status_detail_rows()}
        </table>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-header">Response Time</div>
    <div class="two-col">
      <div class="card">
        <div class="card-title">Distribution</div>
        <div class="chart-wrap"><canvas id="rtimeChart"></canvas></div>
      </div>
      <div class="card">
        <div class="stat-big">
          <div class="stat-big-item">
            <div class="stat-big-label">Avg Response Time</div>
            <div class="stat-big-value" style="color:#3b82f6">{avg_response()}</div>
            <div class="stat-big-sub">milliseconds</div>
          </div>
          <div class="divider"></div>
          <div class="stat-big-item">
            <div class="stat-big-label">Error Rate</div>
            <div class="stat-big-value" style="color:#ef4444">{error_rate()}</div>
            <div class="stat-big-sub">4xx + 5xx responses</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-header">Endpoints</div>
    <div class="two-col">
      <div class="card">
        <div class="card-title">Top 10 by Traffic</div>
        <table>
          <tr><th>#</th><th>Endpoint</th><th>Requests</th><th></th><th>%</th></tr>
          {top_ep_rows()}
        </table>
      </div>
      <div class="card">
        <div class="card-title">Slowest (Avg Response Time)</div>
        <table>
          <tr><th>#</th><th>Endpoint</th><th>Avg Time</th></tr>
          {slow_ep_rows()}
        </table>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-header">Clients</div>
    <div class="two-col">
      <div class="card">
        <div class="card-title">Top IPs by Volume</div>
        <table>
          <tr><th>IP Address</th><th>Requests</th><th>%</th></tr>
          {ip_rows()}
        </table>
      </div>
      <div class="card">
        <div class="card-title">Failed Logins (401) by IP</div>
        <table>
          <tr><th>IP Address</th><th>Attempts</th></tr>
          {failed_rows()}
        </table>
      </div>
    </div>
  </div>

</div>

<script>
const MONO = 'JetBrains Mono';
const GRAY = '#94a3b8';
const GRID = '#f1f5f9';

const fullTrafficLabels = {json.dumps(traffic_labels_short)};
const fullTrafficValues = {json.dumps(traffic_values)};
const displayLabels = {json.dumps(traffic_labels_filtered)};
const displayValues = {json.dumps(traffic_values_filtered)};

new Chart(document.getElementById('trafficChart'), {{
  type: '{chart_type}',
  data: {{
    labels: displayLabels,
    datasets: [{{
      label: 'Requests',
      data: displayValues,
      backgroundColor: '{ '#f97316cc' if use_line else '#f97316' }',
      borderColor: '#ea580c',
      borderWidth: 2,
      borderRadius: {'4' if not use_line else '0'},
      {line_extra}
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          title: function(tooltipItems) {{
            const index = tooltipItems[0].dataIndex;
            let originalLabel = displayLabels[index];
            let actualIndex = -1;
            for (let i = 0; i < fullTrafficLabels.length; i++) {{
              if (fullTrafficLabels[i] === originalLabel) {{
                actualIndex = i;
                break;
              }}
            }}
            if (actualIndex !== -1) {{
              const hour = fullTrafficLabels[actualIndex];
              const count = fullTrafficValues[actualIndex];
              return `${{hour}} - ${{count.toLocaleString()}} requests`;
            }}
            return `${{originalLabel}}`;
          }},
          label: function(context) {{
            return '';
          }}
        }}
      }}
    }},
    scales: {{
      x: {{
        ticks: {{
          color: GRAY,
          font: {{ family: MONO, size: 11 }},
          maxRotation: 45,
          minRotation: 45,
          autoSkip: false
        }},
        grid: {{ display: false }},
        title: {{
          display: true,
          text: 'Hours',
          color: GRAY,
          font: {{ size: 10, family: MONO }}
        }}
      }},
      y: {{
        ticks: {{
          color: GRAY,
          font: {{ family: MONO, size: 11 }},
          callback: function(value) {{
            return value.toLocaleString();
          }}
        }},
        grid: {{ color: GRID }},
        title: {{
          display: true,
          text: 'Number of Requests',
          color: GRAY,
          font: {{ size: 10, family: MONO }}
        }}
      }}
    }}
  }}
}});

new Chart(document.getElementById('statusChart'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(pie_labels)},
    datasets: [{{
      data: {json.dumps(pie_values)},
      backgroundColor: {json.dumps(pie_colors)},
      borderWidth: 0
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{
        position: 'bottom',
        labels: {{ color: '#334155', font: {{ family: 'Inter', size: 12 }}, padding: 16 }}
      }}
    }}
  }}
}});

new Chart(document.getElementById('rtimeChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(rt_labels)},
    datasets: [{{
      data: {json.dumps(rt_values)},
      backgroundColor: ['#3b82f6', '#f59e0b', '#ef4444', '#b91c1c'],
      borderWidth: 0,
      borderRadius: 4
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: GRAY, font: {{ family: MONO, size: 11 }} }}, grid: {{ display: false }} }},
      y: {{ ticks: {{ color: GRAY, font: {{ family: MONO, size: 11 }} }}, grid: {{ color: GRID }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report saved -> {output_path}")