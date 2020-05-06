from flask_restplus import Api
from flask import Blueprint

from app.views.private.dashboard import dashboard_ns
from app.views.private.orderbook import orderbook_ns
from app.views.private.portfolio import portfolio_ns
from app.views.private.upload import upload_ns

private_bp = Blueprint("private_api", __name__)

api = Api(private_bp, decorators=[])

api.add_namespace(dashboard_ns)
api.add_namespace(orderbook_ns)
api.add_namespace(portfolio_ns)
api.add_namespace(upload_ns)
