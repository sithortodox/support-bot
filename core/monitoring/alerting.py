import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Alerter:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.alerts = []
        self.thresholds = {
            "response_time": 5.0,
            "error_rate": 0.1,
            "open_tickets": 100,
            "ai_cost_daily": 10.0,
            "negative_sentiment": 0.3
        }
    
    def check_response_time(self, duration: float, endpoint: str):
        if duration > self.thresholds["response_time"]:
            self.send_alert(
                severity="warning",
                title=f"Slow response: {endpoint}",
                message=f"Response time {duration:.2f}s exceeds threshold {self.thresholds['response_time']}s"
            )
    
    def check_error_rate(self, errors: int, total: int, endpoint: str):
        if total == 0:
            return
        
        rate = errors / total
        if rate > self.thresholds["error_rate"]:
            self.send_alert(
                severity="critical",
                title=f"High error rate: {endpoint}",
                message=f"Error rate {rate:.2%} exceeds threshold {self.thresholds['error_rate']:.2%}"
            )
    
    def check_open_tickets(self, count: int):
        if count > self.thresholds["open_tickets"]:
            self.send_alert(
                severity="warning",
                title="Too many open tickets",
                message=f"Open tickets count {count} exceeds threshold {self.thresholds['open_tickets']}"
            )
    
    def check_ai_cost(self, daily_cost: float):
        if daily_cost > self.thresholds["ai_cost_daily"]:
            self.send_alert(
                severity="warning",
                title="High AI cost",
                message=f"Daily AI cost ${daily_cost:.2f} exceeds threshold ${self.thresholds['ai_cost_daily']:.2f}"
            )
    
    def check_sentiment(self, avg_sentiment: float):
        if avg_sentiment < self.thresholds["negative_sentiment"]:
            self.send_alert(
                severity="info",
                title="Negative sentiment detected",
                message=f"Average sentiment {avg_sentiment:.2f} indicates user frustration"
            )
    
    def send_alert(self, severity: str, title: str, message: str):
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "title": title,
            "message": message
        }
        
        self.alerts.append(alert)
        
        if severity == "critical":
            logger.critical(f"ALERT: {title} - {message}")
        elif severity == "warning":
            logger.warning(f"ALERT: {title} - {message}")
        else:
            logger.info(f"ALERT: {title} - {message}")
        
        self._notify_handlers(alert)
    
    def _notify_handlers(self, alert: Dict[str, Any]):
        webhook_url = self.config.get("webhook_url")
        
        if webhook_url:
            try:
                import aiohttp
                import asyncio
                
                async def send_webhook():
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            webhook_url,
                            json=alert,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status != 200:
                                logger.error(f"Failed to send alert webhook: {response.status}")
                
                asyncio.create_task(send_webhook())
            except Exception as e:
                logger.error(f"Error sending alert webhook: {e}")
    
    def get_alerts(self, limit: int = 50) -> list:
        return self.alerts[-limit:]
    
    def clear_alerts(self):
        self.alerts = []
        logger.info("Alerts cleared")

alerter = Alerter()

def configure_alerter(config: Dict[str, Any]):
    global alerter
    alerter = Alerter(config)
    logger.info("Alerter configured")

def get_alerter() -> Alerter:
    return alerter
