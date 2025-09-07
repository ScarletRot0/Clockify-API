from flask import Flask
from threading import Thread

from app.controllers.webhook_controller import webhook_bp
from app.controllers.user_controller import user_bp
from app.controllers.session_controller import session_bp
from app.controllers.session_binnacle_controller import binnacle_bp
from app.controllers.report_controller import report_bp

from app.extensions import db, mail
from app.config import Config
from app.services.daemon.email_sender_daemon import start_email_sender
from app.services.daemon.monitor_open_sessions import monitor_open_sessions
from app.services.daemon.report_scheduler import start_report_scheduler
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)

    app.register_blueprint(webhook_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(binnacle_bp)
    app.register_blueprint(report_bp)

    def start_monitoring():
        monitor_open_sessions(app)

    def start_reports():
        start_report_scheduler(app)

    def start_email_queue():
        start_email_sender(app)

    with app.app_context():
        Thread(target=start_monitoring, daemon=True).start()
        Thread(target=start_reports, daemon=True).start()
        Thread(target=start_email_queue, daemon=True).start()
    return app