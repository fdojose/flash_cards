#!/usr/bin/env python3
"""
FSRS Integration Dashboard

Web-based dashboard for monitoring FSRS integration performance,
system health, user analytics, and configuration management.
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

DATABASE_PATH = "monitoring/fsrs_monitoring.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('fsrs_dashboard.html')

@app.route('/api/current-status')
def current_status():
    """Get current system status"""
    conn = get_db_connection()
    
    # Get latest metrics
    latest_metrics = conn.execute("""
        SELECT * FROM system_metrics 
        ORDER BY timestamp DESC LIMIT 1
    """).fetchone()
    
    # Get active alerts
    active_alerts = conn.execute("""
        SELECT * FROM alerts 
        WHERE resolved = 0 AND timestamp > datetime('now', '-1 hour')
        ORDER BY timestamp DESC
    """).fetchall()
    
    # Get user performance summary
    user_perf = conn.execute("""
        SELECT * FROM user_performance 
        ORDER BY timestamp DESC LIMIT 1
    """).fetchone()
    
    conn.close()
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'system_health': 'healthy' if len(active_alerts) == 0 else 'warning' if any(alert['severity'] == 'warning' for alert in active_alerts) else 'critical',
        'metrics': dict(latest_metrics) if latest_metrics else {},
        'alerts': [dict(alert) for alert in active_alerts],
        'user_performance': dict(user_perf) if user_perf else {}
    }
    
    return jsonify(status)

@app.route('/api/metrics/history')
def metrics_history():
    """Get historical metrics data"""
    hours = request.args.get('hours', 24, type=int)
    
    conn = get_db_connection()
    
    metrics = conn.execute("""
        SELECT timestamp, integration_efficiency, reconsolidation_rate, 
               response_time_ms, total_users, active_sessions
        FROM system_metrics 
        WHERE timestamp > datetime('now', ? || ' hours')
        ORDER BY timestamp ASC
    """, (f"-{hours}",)).fetchall()
    
    conn.close()
    
    return jsonify([dict(metric) for metric in metrics])

@app.route('/api/alerts/history')
def alerts_history():
    """Get alert history"""
    hours = request.args.get('hours', 24, type=int)
    
    conn = get_db_connection()
    
    alerts = conn.execute("""
        SELECT * FROM alerts 
        WHERE timestamp > datetime('now', ? || ' hours')
        ORDER BY timestamp DESC
    """, (f"-{hours}",)).fetchall()
    
    conn.close()
    
    return jsonify([dict(alert) for alert in alerts])

@app.route('/api/performance/distribution')
def performance_distribution():
    """Get user performance distribution over time"""
    hours = request.args.get('hours', 24, type=int)
    
    conn = get_db_connection()
    
    distribution = conn.execute("""
        SELECT timestamp, high_performers, medium_performers, low_performers
        FROM user_performance 
        WHERE timestamp > datetime('now', ? || ' hours')
        ORDER BY timestamp ASC
    """, (f"-{hours}",)).fetchall()
    
    conn.close()
    
    return jsonify([dict(dist) for dist in distribution])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)
