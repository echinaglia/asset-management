import codecs
import re
from io import BytesIO

import pandas as pd
from flask import request
from flask_restplus import Namespace, Resource

from parser_broker.clear_service.parse_clear import parse_clear_trades
from stock_models.utils.io_utils import session

upload_ns = Namespace("upload")


@upload_ns.route("/")
class Upload(Resource):
    def post(self):
        data = request.json['data']
        filename = request.json['filename']
        data = data.split(',')
        if len(data) != 2:
            return "Erro"
        file_buffer = BytesIO()
        file_buffer.write(codecs.decode(data[1].encode('utf-8'), "base64"))
        file_buffer.seek(0)
        trades, fees = parse_clear_trades({filename: file_buffer})

        owner = 'curado'
        if filename.split('_')[0] == 'eduardo' or '496279' in filename:
            owner = 'eduardo'
        df_ticker_info = pd.read_sql("SELECT ticker, short_name, long_name FROM ticker_info", session().bind)

        fees.rename(columns={"time": "ref_date",
                             "Total CBLC_value": "clbc_value",
                             "Emolumentos_value": "emolumentos_value",
                             "Total Bovespa / Soma_value": "bovespa_value",
                             "Taxa de liquidação_value": "liquidation_value",
                             }, inplace=True)

        replace_words = ["EDJ", "ERJ", "ED", "EJS", "EJ", "ER", "EB", "ES", ",", "-", " "]
        patt = re.compile(r'|'.join(replace_words))
        trades["short_name"] = trades["ticker"].str.replace(patt, "")
        df_ticker_info["short_name"] = df_ticker_info["short_name"].str.replace(patt, "")

        trades = trades.merge(df_ticker_info, on='short_name', how="left")
        trades["brokerage"] = "clear"
        trades["quote_holder"] = owner
        trades["executed"] = True

        trades.drop(columns=["ticker_x"], inplace=True)
        trades.rename(columns={"ticker_y": "ticker"}, inplace=True)
        missed_tickers = {"KROTONONNM": "COGN3.SA", "VIVONNM": "VIVR3.SA", "GAFISADO558": "GFSA3.SA"}
        trades["ticker"].fillna(trades["short_name"].map(missed_tickers), inplace=True)
        if not trades.query('ticker.isnull()').empty:
            print(f"Missing tickers: {trades.query('ticker.isnull()')[['ticker', 'short_name', 'ref_date']]}")
        trades = trades.loc[:, ["ticker", "ref_date", "position", "ammount", "price", "total_value", "executed", "brokerage", "quote_holder"]]
        fees = fees.loc[:, ["ref_date", "clbc_value", "emolumentos_value", "bovespa_value", "liquidation_value", "net_next_day"]]
        fees["brokerage"] = "clear"
        fees["quote_holder"] = owner
        trades.to_sql("trades", session().bind, if_exists='append', schema='public', index=False)
        fees.to_sql("fee_trades", session().bind, if_exists='append', schema='public', index=False)
        print('bla')

        return
