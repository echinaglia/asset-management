import datetime

from flask_restplus import Namespace, Resource

from utils import brl_format, percentage_format
from stock_models.models.daily_quote_holder import DailyQuoteHolder
from stock_models.models.fund_daily_values import DailyFund
from stock_models.models.quote_holder import QuoteHolderMovements
from stock_models.models.yahoo_ticker_value import YahooTickerValue
from stock_models.utils.io_utils import session

dashboard_ns = Namespace("dashboard")


@dashboard_ns.route("/")
class Dashboard(Resource):
    def get(self):
        graph = {'labels': [], 'series': [[], []]}
        all_fund = session().query(DailyFund).order_by(DailyFund.ref_date.asc()).all()
        first = True
        for fund in all_fund:
            yahoo = session().query(YahooTickerValue).filter(YahooTickerValue.ticker == '^BVSP').filter(
                YahooTickerValue.period == 'daily').filter(YahooTickerValue.time == fund.ref_date).one_or_none()

            if not yahoo or fund.ref_date.date().weekday():
                continue
            if first:
                first_fund = fund.quote_price
                first_bvsp = yahoo.close
                first = False
            graph['labels'].append(fund.ref_date.strftime('%m-%y') if fund.ref_date.day <= 8 else '')
            graph['series'][0].append(f'{100 * ((fund.quote_price / first_fund) - 1):.2f}')
            graph['series'][1].append(f'{100 * ((yahoo.close / first_bvsp) - 1):.2f}')

        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        last_friday = (today.date()
                       - datetime.timedelta(days=today.weekday())
                       + datetime.timedelta(days=4, weeks=-1))
        last_month = today.replace(day=1)

        fund = session().query(DailyFund).order_by(DailyFund.ref_date.desc()).all()
        last_week_fund = session().query(DailyFund).filter(DailyFund.ref_date <= last_friday).order_by(
            DailyFund.ref_date.desc()).first()
        last_month_fund = session().query(DailyFund).filter(DailyFund.ref_date < last_month).order_by(
            DailyFund.ref_date.desc()).first()

        quote_holder = session().query(QuoteHolderMovements).all()
        qh_dict = {}
        final_bova, ref_date = session().query(YahooTickerValue.close, YahooTickerValue.time).filter(
            YahooTickerValue.ticker == '^BVSP').filter(
            YahooTickerValue.period == 'daily').order_by(YahooTickerValue.time.desc()).first()
        # final_bova = yahoo.close
        # ref_date = yahoo.time
        for qh in quote_holder:
            try:
                yahoo = session().query(YahooTickerValue).filter(YahooTickerValue.ticker == '^BVSP').filter(
                    YahooTickerValue.period == 'daily').filter(YahooTickerValue.time == qh.time).one()
                if not qh.name in qh_dict.keys():
                    qh_dict[qh.name] = {'bova': 0, 'sum': 0}
                qh_dict[qh.name]['bova'] = qh_dict[qh.name]['bova'] + qh.value * final_bova / yahoo.close
                qh_dict[qh.name]['sum'] = qh_dict[qh.name]['sum'] + qh.value
            except:
                print(qh.time)
        daily_qh = session().query(DailyQuoteHolder).filter(DailyQuoteHolder.ref_date == ref_date).order_by(
            DailyQuoteHolder.pl.desc()).all()
        quote_holder = {
            'header': ['Name', 'Quote Amount', 'Value', 'Return', 'Ibovespa'],
            'data': [],
        }
        for dqh in daily_qh:
            quote_holder['data'].append([dqh.name, f'{dqh.amount:.2f}', brl_format(dqh.pl),
                                         percentage_format(100 * (dqh.pl / qh_dict[dqh.name]['sum'] - 1)),
                                         percentage_format(100 * (qh_dict[dqh.name]['bova'] / qh_dict[dqh.name]['sum'] - 1))])

        table = {
            'patrimonial_equity': brl_format(fund[0].pl),
            'ref_date': fund[0].ref_date.strftime('%Y-%m-%d'),
            'cash': brl_format(fund[0].cash),
            'quote_amount': f'{fund[0].amount:.2f}',
            'quote_price': brl_format(fund[0].quote_price),
            'return': {
                'daily': [percentage_format(fund[0].pl / fund[1].pl), fund[1].ref_date.strftime('%Y-%m-%d')],
                'weekly': [percentage_format(fund[0].pl / last_week_fund.pl),
                           last_week_fund.ref_date.strftime('%Y-%m-%d')],
                'monthly': [percentage_format(fund[0].pl / last_month_fund.pl),
                            last_month_fund.ref_date.strftime('%Y-%m-%d')],
            },
            'graph': graph,
            'legend': {
                'names': ['Fund', 'Ibovespa'],
                'types': ['info', 'danger']
            },
            'quote_holder': quote_holder
        }
        return table
