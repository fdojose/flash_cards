#!/usr/bin/env python3
"""
FSRS Integration Monitoring System

Continuous monitoring system for FSRS integration performance,
system health, and configuration effectiveness tracking.
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Configuration
BACKEND_URL = "http://localhost:8000"
MONITORING_INTERVAL = 300  # 5 minutes
ALERT_THRESHOLDS = {
    'integration_efficiency_min': 60.0,  # Alert if below 60%
    'reconsolidation_rate_max': 25.0,    # Alert if above 25%
    'response_time_max': 2000,           # Alert if above 2 seconds
    'error_rate_max': 5.0,               # Alert if above 5%
    'stability_score_min': 0.8           # Alert if average below 0.8
}

# Email configuration (set these environment variables)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
ALERT_RECIPIENTS = os.getenv('ALERT_RECIPIENTS', '').split(',')

class FSRSMonitor:
    """FSRS Integration monitoring system"""
    
    def __init__(self):
        self.db_path = "monitoring/fsrs_monitoring.db"
        self.setup_database()
        
    def setup_database(self):
        """Initialize monitoring database"""
        os.makedirs("monitoring", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create monitoring tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_users INTEGER,
                active_sessions INTEGER,
                integration_efficiency REAL,
                reconsolidation_rate REAL,
                response_time_ms REAL,
                error_rate REAL,
                config_hash TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                metric_value REAL,
                threshold_value REAL,
                resolved BOOLEAN DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_count INTEGER,
                high_performers INTEGER,
                medium_performers INTEGER,
                low_performers INTEGER,
                avg_stability_score REAL
            )
        """)
        
        conn.commit()
        conn.close()
        
    def collect_system_metrics(self) -> Optional[Dict]:
        """Collect system-wide FSRS performance metrics"""
        try:
            # Make request to admin performance endpoint
            response = requests.get(
                f"{BACKEND_URL}/admin/fsrs-performance",
                headers={"Authorization": "Bearer admin-token"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log_error(f"Failed to collect metrics: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_error(f"Request error collecting metrics: {str(e)}")
            return None
            
    def analyze_metrics(self, metrics: Dict) -> List[Dict]:
        """Analyze metrics and identify alerts"""
        alerts = []
        
        # Integration efficiency check
        if metrics.get('overall_integration_efficiency', 100) < ALERT_THRESHOLDS['integration_efficiency_min']:
            alerts.append({
                'type': 'integration_efficiency_low',
                'severity': 'warning',
                'message': f"Integration efficiency below threshold: {metrics['overall_integration_efficiency']:.1f}%",
                'value': metrics['overall_integration_efficiency'],
                'threshold': ALERT_THRESHOLDS['integration_efficiency_min']
            })
            
        # Reconsolidation rate check
        if metrics.get('overall_reconsolidation_rate', 0) > ALERT_THRESHOLDS['reconsolidation_rate_max']:
            alerts.append({
                'type': 'reconsolidation_rate_high',
                'severity': 'critical',
                'message': f"Reconsolidation rate above threshold: {metrics['overall_reconsolidation_rate']:.1f}%",
                'value': metrics['overall_reconsolidation_rate'],
                'threshold': ALERT_THRESHOLDS['reconsolidation_rate_max']
            })
            
        # Response time check
        if metrics.get('average_response_time_ms', 0) > ALERT_THRESHOLDS['response_time_max']:
            alerts.append({
                'type': 'response_time_high',
                'severity': 'warning',
                'message': f"Response time above threshold: {metrics['average_response_time_ms']:.0f}ms",
                'value': metrics['average_response_time_ms'],
                'threshold': ALERT_THRESHOLDS['response_time_max']
            })
            
        # Error rate check
        if metrics.get('error_rate', 0) > ALERT_THRESHOLDS['error_rate_max']:
            alerts.append({
                'type': 'error_rate_high',
                'severity': 'critical',
                'message': f"Error rate above threshold: {metrics['error_rate']:.1f}%",
                'value': metrics['error_rate'],
                'threshold': ALERT_THRESHOLDS['error_rate_max']
            })
            
        # Performance distribution check
        total_performers = (metrics.get('high_performers', 0) + 
                           metrics.get('medium_performers', 0) + 
                           metrics.get('low_performers', 0))
        
        if total_performers > 0:
            low_performer_percentage = (metrics.get('low_performers', 0) / total_performers) * 100
            if low_performer_percentage > 30:  # Alert if more than 30% are low performers
                alerts.append({
                    'type': 'low_performer_percentage_high',
                    'severity': 'warning',
                    'message': f"High percentage of low performers: {low_performer_percentage:.1f}%",
                    'value': low_performer_percentage,
                    'threshold': 30.0
                })
                
        return alerts
        
    def store_metrics(self, metrics: Dict):
        """Store metrics in monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_metrics 
            (total_users, active_sessions, integration_efficiency, reconsolidation_rate,
             response_time_ms, error_rate, config_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.get('total_users', 0),
            metrics.get('active_integration_sessions', 0),
            metrics.get('overall_integration_efficiency', 0),
            metrics.get('overall_reconsolidation_rate', 0),
            metrics.get('average_response_time_ms', 0),
            metrics.get('error_rate', 0),
            metrics.get('current_config_hash', '')
        ))
        
        cursor.execute("""
            INSERT INTO user_performance
            (user_count, high_performers, medium_performers, low_performers, avg_stability_score)
            VALUES (?, ?, ?, ?, ?)
        """, (
            metrics.get('total_users', 0),
            metrics.get('high_performers', 0),
            metrics.get('medium_performers', 0),
            metrics.get('low_performers', 0),
            0.0  # avg_stability_score would need separate calculation
        ))
        
        conn.commit()
        conn.close()
        
    def store_alerts(self, alerts: List[Dict]):
        """Store alerts in database"""
        if not alerts:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute("""
                INSERT INTO alerts (alert_type, severity, message, metric_value, threshold_value)
                VALUES (?, ?, ?, ?, ?)
            """, (
                alert['type'],
                alert['severity'],
                alert['message'],
                alert['value'],
                alert['threshold']
            ))
            
        conn.commit()
        conn.close()
        
    def send_alert_email(self, alerts: List[Dict]):
        """Send email alerts for critical issues"""
        if not alerts or not EMAIL_USER or not ALERT_RECIPIENTS:
            return
            
        # Filter for critical alerts only
        critical_alerts = [alert for alert in alerts if alert['severity'] == 'critical']
        if not critical_alerts:
            return
            
        try:
            msg = MimeMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = ', '.join(ALERT_RECIPIENTS)
            msg['Subject'] = f"FSRS Integration Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            body = "FSRS Integration System Alert\n"
            body += "=" * 40 + "\n\n"
            
            for alert in critical_alerts:
                body += f"🚨 {alert['severity'].upper()}: {alert['message']}\n"
                body += f"   Current: {alert['value']}\n"
                body += f"   Threshold: {alert['threshold']}\n\n"
                
            body += f"Timestamp: {datetime.now()}\n"
            body += f"Server: {BACKEND_URL}\n"
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            self.log_info(f"Alert email sent for {len(critical_alerts)} critical alerts")
            
        except Exception as e:
            self.log_error(f"Failed to send alert email: {str(e)}")
            
    def generate_health_report(self) -> str:
        """Generate system health report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent metrics (last 24 hours)
        cursor.execute("""
            SELECT AVG(integration_efficiency), AVG(reconsolidation_rate), 
                   AVG(response_time_ms), COUNT(*) as samples
            FROM system_metrics 
            WHERE timestamp > datetime('now', '-24 hours')
        """)
        
        result = cursor.fetchone()
        if result and result[3] > 0:  # If we have samples
            avg_efficiency, avg_recon_rate, avg_response_time, sample_count = result
            
            report = f"""
FSRS Integration Health Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 70}

📊 24-Hour Performance Summary:
• Integration Efficiency: {avg_efficiency:.1f}% (Target: ≥{ALERT_THRESHOLDS['integration_efficiency_min']:.0f}%)
• Reconsolidation Rate: {avg_recon_rate:.1f}% (Target: ≤{ALERT_THRESHOLDS['reconsolidation_rate_max']:.0f}%)
• Average Response Time: {avg_response_time:.0f}ms (Target: ≤{ALERT_THRESHOLDS['response_time_max']:.0f}ms)
• Data Samples: {sample_count}

"""
        else:
            report = f"""
FSRS Integration Health Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 70}

⚠️  No recent metrics data available.
"""
        
        # Get recent alerts
        cursor.execute("""
            SELECT alert_type, COUNT(*) as count, MAX(timestamp) as last_seen
            FROM alerts 
            WHERE timestamp > datetime('now', '-24 hours') AND resolved = 0
            GROUP BY alert_type
            ORDER BY count DESC
        """)
        
        alert_summary = cursor.fetchall()
        if alert_summary:
            report += "🚨 Active Alerts (24 hours):\n"
            for alert_type, count, last_seen in alert_summary:
                report += f"• {alert_type}: {count} occurrences (last: {last_seen})\n"
        else:
            report += "✅ No active alerts in the last 24 hours.\n"
            
        conn.close()
        return report
        
    def log_info(self, message: str):
        """Log info message"""
        print(f"[{datetime.now()}] INFO: {message}")
        
    def log_error(self, message: str):
        """Log error message"""
        print(f"[{datetime.now()}] ERROR: {message}")
        
    def run_monitoring_cycle(self):
        """Run single monitoring cycle"""
        self.log_info("Starting FSRS monitoring cycle")
        
        # Collect metrics
        metrics = self.collect_system_metrics()
        if not metrics:
            self.log_error("Failed to collect system metrics")
            return
            
        # Store metrics
        self.store_metrics(metrics)
        
        # Analyze for alerts
        alerts = self.analyze_metrics(metrics)
        
        if alerts:
            self.log_info(f"Generated {len(alerts)} alerts")
            self.store_alerts(alerts)
            self.send_alert_email(alerts)
            
            # Print alerts to console
            for alert in alerts:
                if alert['severity'] == 'critical':
                    self.log_error(alert['message'])
                else:
                    print(f"[{datetime.now()}] WARNING: {alert['message']}")
        else:
            self.log_info("No alerts generated - system healthy")
            
        # Log current metrics
        self.log_info(f"Metrics - Efficiency: {metrics.get('overall_integration_efficiency', 0):.1f}%, "
                     f"Reconsolidation: {metrics.get('overall_reconsolidation_rate', 0):.1f}%, "
                     f"Users: {metrics.get('total_users', 0)}")
                     
    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        self.log_info(f"Starting FSRS continuous monitoring (interval: {MONITORING_INTERVAL}s)")
        
        while True:
            try:
                self.run_monitoring_cycle()
                time.sleep(MONITORING_INTERVAL)
                
            except KeyboardInterrupt:
                self.log_info("Monitoring stopped by user")
                break
            except Exception as e:
                self.log_error(f"Monitoring cycle error: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying
                
def main():
    """Main monitoring function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        # Generate and print health report
        monitor = FSRSMonitor()
        report = monitor.generate_health_report()
        print(report)
        return
        
    # Run continuous monitoring
    monitor = FSRSMonitor()
    monitor.run_continuous_monitoring()

if __name__ == "__main__":
    main()
