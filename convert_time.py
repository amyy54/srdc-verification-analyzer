from datetime import datetime, timedelta 
from dateutil.relativedelta import relativedelta


def convert_time(time):
    now = datetime.now()
    if time == "lastmonth":
        last_month_date = now + relativedelta(months=-1)
        return last_month_date.strftime('%Y-%m-%d')
    elif time == "lastday":
        last_day_date = now + relativedelta(days=-1)
        return last_day_date.strftime('%Y-%m-%d')
    elif time == "lastweek":
        last_week_date = now + relativedelta(days=-7)
        return last_week_date.strftime('%Y-%m-%d')
    
    elif time == "thismonth":
        return now.replace(day=1).strftime('%Y-%m-%d')
    elif time == "thisday":
        return now.strftime('%Y-%m-%d')
    elif time == "thisweek":
        return (now - timedelta(days=(now.weekday() + 1) % 7)).strftime('%Y-%m-%d')
    elif time == "thisweekmondaystart":
        return (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')

    else:
        return None
