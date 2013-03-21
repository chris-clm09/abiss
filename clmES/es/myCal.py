import sys
import datetime
import locale as _locale

__all__ = ["IllegalMonthError", "IllegalWeekdayError", "setfirstweekday",
           "firstweekday", "isleap", "leapdays", "weekday", "monthrange",
           "monthcalendar", "prmonth", "month", "prcal", "calendar",
           "timegm", "month_name", "month_abbr", "day_name", "day_abbr"]

# Exception raised for bad input (with string parameter for details)
error = ValueError

# Exceptions raised for bad input
class IllegalMonthError(ValueError):
    def __init__(self, month):
        self.month = month
    def __str__(self):
        return "bad month number %r; must be 1-12" % self.month


class IllegalWeekdayError(ValueError):
    def __init__(self, weekday):
        self.weekday = weekday
    def __str__(self):
        return "bad weekday number %r; must be 0 (Monday) to 6 (Sunday)" % self.weekday


# Constants for months referenced later
January = 1
February = 2

# Number of days per month (except for February in leap years)
mdays = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

class Calendar(object):
    """
    Base calendar class. This class doesn't do any formatting. It simply
    provides data to subclasses.
    """

    def __init__(self, firstweekday=0):
        self.firstweekday = firstweekday # 0 = Monday, 6 = Sunday

    def getfirstweekday(self):
        return self._firstweekday % 7

    def setfirstweekday(self, firstweekday):
        self._firstweekday = firstweekday

    firstweekday = property(getfirstweekday, setfirstweekday)

    def iterweekdays(self):
        """
        Return a iterator for one week of weekday numbers starting with the
        configured first one.
        """
        for i in range(self.firstweekday, self.firstweekday + 7):
            yield i%7

    #====================================================================================
    # Day of the week...starting at 1 for monday
    #====================================================================================
    def datetoday(self, day, month, year):
        d = day
        m = month
        y = year
        if m < 3:
            z = y-1
        else:
            z = y
        dayofweek = ( 23*m//9 + d + 4 + y + z//4 - z//100 + z//400 )
        if m >= 3:
            dayofweek -= 2
        dayofweek = dayofweek%7
        return dayofweek

    def itermonthdatesdays(self, year, month, theday):
        """
        Return an iterator for one month. The iterator will yield datetime.date
        values and will always iterate through complete weeks, so it will yield
        dates outside the specified month.
        """
        date = datetime.date(year, month, 1)
        # Go back to the beginning of the week
        days = (date.weekday() - self.firstweekday) % 7
        date -= datetime.timedelta(days=days)
        oneday = datetime.timedelta(days=1)
        while True:
            if date.month == month:
                if self.datetoday(date.day, date.month, date.year) == theday:
                    yield date
            try:
                date += oneday
            except OverflowError:
                # Adding one day could fail after datetime.MAXYEAR
                break
            if date.month != month and date.weekday() == self.firstweekday:
                break
            
if __name__ == "__main__":
    #main(sys.argv)
    c = Calendar()
    #for i in c.itermonthdatesdays(2012, 11, 3):
     #   print i
        
    for t in c.itermonthdatesdays(2012, 2, 3):
        print t
    