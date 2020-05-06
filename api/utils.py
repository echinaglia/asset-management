import datetime
import pytz
from flask import abort, jsonify, make_response


def brl_format(value):
    return f'R$ {value:.2f}'


def percentage_format(value):
    return f'{value:.2f} %'


def now():
    return datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))


def badrequest(message="bad request.", **kwargs):
    abort(make_response(jsonify(message=message, **kwargs), 400))
