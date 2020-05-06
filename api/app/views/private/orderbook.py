from dateutil.relativedelta import relativedelta
from flask import request
from flask_restplus import Namespace, Resource

from utils import badrequest, brl_format, percentage_format, now
from stock_models.models.daily_open import DailyOpen
from stock_models.models.fund_daily_values import DailyFund
from stock_models.models.model_signal import ModelSignal
from stock_models.utils.io_utils import session
from datetime import datetime

orderbook_ns = Namespace("orderbook")


@orderbook_ns.route("/")
class Orderbook(Resource):
    def get(self):
        ref_date = now() + relativedelta(days=1)
        sell_ticker = session().query(ModelSignal).filter(ModelSignal.sell_date.is_(None))
        sell_ticker = sell_ticker.filter(ModelSignal.executed.is_(True))
        sell_ticker = sell_ticker.filter(ModelSignal.start_watch < ref_date.date()).all()

        sell_data = []
        for sell in sell_ticker:
            info = [
                sell.ticker, sell.start_watch.strftime('%d-%m-%Y'), sell.expected_close.strftime('%d-%m-%Y'),
                sell.amount, brl_format(sell.buy_price * (1 + sell.stop_loss)),
                brl_format(sell.buy_price * (1 + sell.take_profit)), str(sell.sell_price).replace('.', ',')
            ]
            sell_data.append(info)

        buy_ticker = session().query(ModelSignal).filter(ModelSignal.executed.is_(None))
        buy_ticker = buy_ticker.order_by(ModelSignal.rank_day.asc()).limit(10).all()
        buy_data = []
        fund = session().query(DailyFund).order_by(DailyFund.ref_date.desc()).first()
        for buy in buy_ticker:
            open = session().query(DailyOpen).filter(DailyOpen.ticker == buy.ticker)
            open = open.filter(DailyOpen.ref_date == fund.ref_date).one_or_none()
            conc = open.total_value / fund.pl if open else 0
            info = [buy.ticker, f'{buy.predicted:.2f}', percentage_format(conc),
                    buy.amount, str(buy.buy_price).replace('.', ',')]
            buy_data.append(info)

        table = {
            'sell': {
                'header': ['Ticker', 'Start Watch', 'Expected Close', 'Amount', 'Stop Price', 'Target Price',
                           'Sell Value'],
                'data': sell_data,
                'ref_date': ref_date.strftime('%d-%m-%Y')
            },
            'buy': {
                'header': ['Ticker', 'Predicted', 'Portfolio %', 'Amount', 'Buy Price'],
                'data': buy_data,
                'ref_date': fund.ref_date.strftime('%d-%m-%Y')
            }
        }

        return table

    def post(self):
        data = request.json['data']
        _type = request.json['type']
        today = now().date()
        if _type == 'buy':
            # Buy Example
            # ["BEEF3.SA", "0.51", "0.12 %", 400, "7,79"]
            buy_ticker = session().query(ModelSignal).filter(ModelSignal.executed.is_   (None))
            buy_ticker = buy_ticker.filter(ModelSignal.ticker == data[0]).one_or_none()
            if not buy_ticker:
                badrequest('Buy trade not found')

            buy_ticker.amount = data[3]
            buy_ticker.buy_price = float(data[4].replace(',', '.'))
            buy_ticker.executed = True
            buy_ticker.buy_date = today

        elif _type == 'sell':
            # Sell Example
            # ["CMIG4.SA", "24-03-2020", "02-04-2020", 300, "R$ 8.83", "R$ 9.35", "8,82"]
            sell_ticker = session().query(ModelSignal).filter(ModelSignal.sell_date.is_(None))
            sell_ticker = sell_ticker.filter(ModelSignal.ticker == data[0])
            sell_ticker = sell_ticker.filter(ModelSignal.start_watch == datetime.strptime(data[1], '%d-%m-%Y'))
            sell_ticker = sell_ticker.filter(ModelSignal.expected_close == datetime.strptime(data[2], '%d-%m-%Y'))
            sell_ticker = sell_ticker.filter(ModelSignal.amount == data[3]).one_or_none()
            if not sell_ticker:
                badrequest('Sell trade not found')
            sell_ticker.sell_price = float(data[6].replace(',', '.'))
            sell_ticker.sell_date = today

        else:
            badrequest('Invalid trade type')

        return 'Success'
