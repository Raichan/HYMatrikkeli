# -*- coding: UTF-8 -*-

def date_with_zeros(date):
    if(len(date) == 1):
        date = "0" + date
    return date