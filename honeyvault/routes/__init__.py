"""Pendaftaran blueprint pada aplikasi Flask."""

from honeyvault.routes.dashboard import bp as dashboard_bp
from honeyvault.routes.evaluation import bp as evaluation_bp
from honeyvault.routes.simulation import bp as simulation_bp


def register_blueprints(app):
    """Mendaftarkan seluruh blueprint ke aplikasi."""
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(evaluation_bp)
    return app
