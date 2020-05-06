from flask_restplus import Namespace, Resource
from sqlalchemy.sql import func

from utils import brl_format, percentage_format
from stock_models.models.daily_open import DailyOpen
from stock_models.models.ticker_info import TickerInfo
from stock_models.utils.io_utils import session

portfolio_ns = Namespace("portfolio")


@portfolio_ns.route("/")
class Portfolio(Resource):
    def get(self):
        date = session().query(DailyOpen.ref_date).order_by(DailyOpen.ref_date.desc()).first()
        total = session().query(func.sum(DailyOpen.total_value), func.sum(DailyOpen.amount)).filter(
            DailyOpen.ref_date == date).one()
        daily_open = session().query(DailyOpen).filter(DailyOpen.ref_date == date).all()

        subsectors = session().query(TickerInfo.subsector, func.sum(DailyOpen.total_value))
        subsectors = subsectors.join(DailyOpen, DailyOpen.ticker == TickerInfo.ticker)
        subsectors = subsectors.filter(DailyOpen.ref_date == date).group_by(TickerInfo.subsector).all()

        ticker = []
        for do in daily_open:
            ticker.append([do.ticker, do.amount, brl_format(do.total_value), percentage_format(100 * do.total_value / total[0])])

        subsector = []
        for sb in subsectors:
            subsector.append([sb[0] or 'Ibovespa', brl_format(sb[1]), percentage_format(100 * sb[1] / total[0])])

        table = {
            'ticker': {
                'header': ['Ticker', 'Amount', 'Value', 'Concentration'],
                'data': ticker,
                'total': ['Total', total[1], brl_format(total[0]), percentage_format(100)]
            },
            'subsector': {
                'header': ['Ticker', 'Value', 'Concentration'],
                'data': subsector,
                'total': ['Total', brl_format(total[0]), percentage_format(100)]
            },
            'ref_date': date[0].strftime('%d-%m-%Y')
        }
        return table
