#! /usr/bin/env python
# iso-8859-1 -*
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02110-1301, USA.
#
# Crontab-like string parse. Inspired on crontab.py of the
# gnome-schedule-1.1.0 package.
#
# Edited by Robinson Farrar (RFDaemoniac) July 2011
#

import re
import datetime

class SimpleCrontabEntry(object):
    """Contrab-like parser.

    Only deals with the first 5 fields of a normal crontab
    entry."""

    def __init__(self, entry, expiration = 0):
        self.__setup_timespec()
        self.set_value(entry)
        self.set_expiration(expiration)

    def set_expiration(self, val):
        self.expiration = datetime.timedelta(minutes=val)

    def set_value(self, entry):
        self.data = entry
        fields = re.findall("\S+", self.data)
        if len(fields) != 5 :
            raise ValueError("Crontab entry needs 5 fields")
        self.fields = {
            "minute" : fields[0],
            "hour"   : fields[1],
            "day"    : fields[2],
            "month"  : fields[3],
            "weekday": fields[4],
            }
        if not self._is_valid():
            raise ValueError("Bad Entry")

    #### HERE BEGINS THE CODE BORROWED FROM gnome-schedule ###
    def __setup_timespec(self):

        self.special = {
                "@reboot"  : '',
                "@hourly"  : '0 * * * *',
                "@daily"   : '0 0 * * *',
                "@weekly"  : '0 0 * * 0',
                "@monthly" : '0 0 1 * *',
                "@yearly"  : '0 0 1 1 *'
                }

        self.timeranges = {
                "minute"   : range(0,60),
                "hour"     : range(0,24),
                "day"      : range(1,32),
                "month"    : range(1,13),
                "weekday"  : range(0,8)
                }

        self.timenames = {
                "minute"   : "Minute",
                "hour"     : "Hour",
                "day"      : "Day of Month",
                "month"    : "Month",
                "weekday"  : "Weekday"
                }

        self.monthnames = {
                "1"        : "Jan",
                "2"        : "Feb",
                "3"        : "Mar",
                "4"        : "Apr",
                "5"        : "May",
                "6"        : "Jun",
                "7"        : "Jul",
                "8"        : "Aug",
                "9"        : "Sep",
                "10"       : "Oct",
                "11"       : "Nov",
                "12"       : "Dec"
                }

        self.downames = {
                "0"        : "Sun",
                "1"        : "Mon",
                "2"        : "Tue",
                "3"        : "Wed",
                "4"        : "Thu",
                "5"        : "Fri",
                "6"        : "Sat",
                "7"        : "Sun"
                }

    def checkfield (self, expr, type):
        """Verifies format of Crontab timefields

        Checks a single Crontab time expression.
        At first possibly contained alias names will be replaced by their
        corresponding numbers. After that every asterisk will be replaced by
        a "first to last" expression. Then the expression will be splitted
        into the komma separated subexpressions.

        Each subexpression will run through: 
        1. Check for stepwidth in range (if it has one)
        2. Check for validness of range-expression (if it is one)
        3. If it is no range: Check for simple numeric
        4. If it is numeric: Check if it's in range

        If one of this checks failed, an exception is raised. Otherwise it will
        do nothing. Therefore this function should be used with 
        a try/except construct.  
        """

        timerange = self.timeranges[type]

        # Replace alias names only if no leading and following alphanumeric and 
        # no leading slash is present. Otherwise terms like "JanJan" or 
        # "1Feb" would give a valid check. Values after a slash are stepwidths
        # and shouldn't have an alias.
        if type == "month": alias = self.monthnames.copy()
        elif type == "weekday": alias = self.downames.copy()
        else: alias = None
        if alias != None:
            while True:
                try: key,value = alias.popitem()
                except KeyError: break
                expr = re.sub("(?<!\w|/)" + value + "(?!\w)", key, expr)

        expr = expr.replace("*", str(min(timerange)) + "-" + str(max(timerange)) )

        lst = expr.split(",")
        rexp_step = re.compile("^(\d+-\d+)/(\d+)$")
        rexp_range = re.compile("^(\d+)-(\d+)$")

        expr_range = []
        for field in lst:
            # Extra variables for time calculation
            step = None
            buff = None

            result = rexp_step.match(field)
            if  result != None:
                field = result.groups()[0]
                # We need to take step in count
                step = int(result.groups()[1])
                if step not in timerange:
                    raise ValueError("stepwidth",
                                     self.timenames[type],
                                     "Must be between %(min)s and %(max)s" % { "min": min(timerange),
                                                                               "max": max(timerange) } )

            result = rexp_range.match(field)
            if (result != None):
                if (int(result.groups()[0]) not in timerange) or (int(result.groups()[1]) not in timerange):
                    raise ValueError("range",
                                     self.timenames[type],
                                     "Must be between %(min)s and %(max)s" % { "min": min(timerange),
                                                                               "max": max(timerange) } )
                # Now we deal with a range...
                if step != None :
                    buff = range(int(result.groups()[0]), int(result.groups()[1])+1, step)
                else :
                    buff = range(int(result.groups()[0]), int(result.groups()[1])+1)

            elif not field.isdigit():
                raise ValueError("fixed",
                                 self.timenames[type],
                                 "%s is not a number" % ( field ) )
            elif int(field) not in timerange:
                raise ValueError("fixed",
                                 self.timenames[type],
                                 "Must be between %(min)s and %(max)s" % { "min": min(timerange),
                                                                           "max": max(timerange) } )
            if buff != None :
                expr_range.extend(buff)
            else :
                expr_range.append(int(field))

        expr_range.sort()
        # Here we may need to check wether some elements have duplicates
        self.fields[type] = expr_range


    #### HERE ENDS THE CODE BORROWED FROM gnome-schedule ###

    def _is_valid(self):
        """Validates the data to check for a well-formated cron
        entry.
        Returns True or false"""

        try:
            for typ, exp in self.fields.items():
                self.checkfield(exp, typ)
        except ValueError,(specific,caused,explanation):
            print "PROBLEM TYPE: %s, ON FIELD: %s -> %s " % (specific,caused,explanation)
            return False
        return True

    def __next_time(self, time_list, time_now):
        """Little helper function to find next element on the list"""
        tmp = [x for x in time_list if x >= time_now]
        carry = False
        if len(tmp) == 0:
            carry = True
            sol = time_list[0]
        else:
            sol = tmp[0]
        return sol, carry

    def __prev_time(self, time_list, item):
        """Little helper function to find previous element on the list"""
        pos = time_list.index(item)
        elem = time_list[pos-1]
        carry = elem >= time_list[pos]
        return elem, carry

    def __next_month(self, month, sol):
        """Find next month of execution given the month arg. If month
        is different than current calls all the other __next_*
        functions to set up the time."""

        sol['month'], carry = self.__next_time(self.fields['month'], month)
        if carry :
            sol['year'] += 1
        if sol['month'] != month :
            self.__next_day(1,sol)
            self.__next_hour(0,sol)
            self.__next_minute(0,sol)
            return False
        return True

    def __next_minute(self, minute, sol):
        """Find next minute of execution given the minute arg."""
        sol['minute'], carry = self.__next_time(self.fields['minute'], minute)
        if carry:
            self.__next_hour(sol['hour']+1, sol)
        return True

    def __next_hour(self, hour, sol):
        """Find next hour of execution given the hour arg. If hour is
        different than current calls the __next_hour function to set
        up the minute """

        sol['hour'], carry = self.__next_time(self.fields['hour'], hour)
        if carry:
            self.__next_day(sol['day']+1, sol)
        if sol['hour'] != hour:
            self.__next_minute(0,sol)
            return False
        return True

    #el weekday se calcula a partir del dia, el mes y ao dentro de sol
    def __next_day(self, day, sol):
        """Find next day of execution given the day and the month/year
        information held on the sol arg. If day is different than
        current calls __next_hour and __next_minute functions to set
        them to the correct values"""

        try:
            now = datetime.date(sol['year'], sol['month'], day)
        except:
            try:
                now = datetime.date(sol['year'], sol['month']+1, 1)
            except:
                now = datetime.date(sol['year']+1, 1, 1)
        # The way is handled on the system is monday = 0, but for crontab sunday =0
        weekday = now.weekday()+1
        # first calculate day
        day_tmp, day_carry = self.__next_time(self.fields['day'], day)
        day_diff = datetime.date(sol['year'], sol['month'], day_tmp) - now

        # if we have all days but we don't have all weekdays we need to
        # perform different
        if len(self.fields['day']) == 31 and len(self.fields['weekday']) != 8:
            weekday_tmp, weekday_carry = self.__next_time(self.fields['weekday'], weekday)
            # Both 0 and 7 represent sunday
            weekday_tmp -= 1
            if weekday_tmp < 0 : weekday_tmp = 6
            weekday_diff = datetime.timedelta(days=weekday_tmp - (weekday - 1))
            if weekday_carry :
                weekday_diff += datetime.timedelta(weeks=1)
            weekday_next_month = (now + weekday_diff).month != now.month
            # If next weekday is not on the next month
            if not weekday_next_month :
                sol['day'] = (now + weekday_diff).day
                if sol['day'] != day :
                    self.__next_hour(0,sol)
                    self.__next_minute(0, sol)
                    return False
                return True
            else :
                flag = self.__next_month(sol['month']+1, sol)
                if flag :
                    return self.__next_day(0, sol)
                return False

        # if we don't have all the weekdays means that we need to use
        # them to calculate next day
        if len(self.fields['weekday']) != 8:
            weekday_tmp, weekday_carry = self.__next_time(self.fields['weekday'], weekday)
            # Both 0 and 7 represent sunday
            weekday_tmp -= 1
            if weekday_tmp < 0 : weekday_tmp = 6
            weekday_diff = datetime.timedelta(days=weekday_tmp - (weekday - 1))
            if weekday_carry :
                weekday_diff += datetime.timedelta(weeks=1)
            weekday_next_month = (now + weekday_diff).month != now.month
            # If next weekday is not on the next month
            if not weekday_next_month :
                #  If the next day is on other month, the next weekday
                #  is closer to happen so is what we choose
                if day_carry:
                    sol['day'] = (now + weekday_diff).day
                    if sol['day'] != day :
                        self.__next_hour(0,sol)
                        self.__next_minute(0, sol)
                        return False
                    return True
                else :
                    # Both day and weekday are good candidates, let's
                    # find out who is going to happen
                    # sooner
                    diff = min(day_diff, weekday_diff)
                    sol['day'] = (now+diff).day
                    if sol['day'] != day :
                        self.__next_hour(0,sol)
                        self.__next_minute(0, sol)
                        return False
                    return True

        sol['day'] = day_tmp
        if day_carry :
            self.__next_month(sol['month']+1, sol)
        if sol['day'] != day :
            self.__next_hour(0,sol)
            self.__next_minute(0, sol)
            return False
        return True

    
    def matches(self, time = datetime.datetime.now()):
        """Checks if given time matches cron pattern."""
        return time.month in self.fields['month'] and \
            time.day in self.fields['day'] and \
            time.hour in self.fields['hour'] and \
            time.minute in self.fields['minute'] and \
            time.weekday() + 1 in [d or 7 for d in self.fields['weekday']] # Sunday may be represented as ``0`` or ``7``.


    def next_run(self, time = datetime.datetime.now()):
        """Calculates when will the next execution be."""
        if self.matches(time):
            time += datetime.timedelta(minutes = 1)
        sol = {'minute': time.minute, 'hour': time.hour, 'day': time.day, 'month' : time.month, 'year' : time.year}
        # next_month if calculated first as next_day depends on
        # it. Also if next_month is different than time.month the
        # function will set up the rest of the fields
        try:
            self.__next_month(time.month, sol) and \
                                          self.__next_day(time.day, sol) and \
                                          self.__next_hour(time.hour, sol) and \
                                          self.__next_minute(time.minute, sol)
            return datetime.datetime(sol['year'], sol['month'], sol['day'], sol['hour'], sol['minute'])
        except:
            try:
                return self.next_run(datetime.datetime(time.year, time.month+1, 1, 0, 0))
            except:
                return self.next_run(datetime.datetime(time.year+1, 1, 1, 0, 0))

    def __prev_date(self, base, prev_day, carry_day):
        if carry_day:
            prev_month=base.month
            prev_year=base.year
            i = 0
            for i in xrange(7):
                prev_month, carry_month = self.__prev_time(self.fields['month'], prev_month)
                if carry_month:
                    prev_year -= 1
                try:
                    date = datetime.datetime(prev_year, prev_month, prev_day, base.hour, base.minute)
                except ValueError:
                    pass
                else:
                    if date.weekday() in self.fields['weekday']:
                        base = date
                        break
            else:
                raise ValueError('Can\'t find previous run time for date %s' % base)
        else:
            base = datetime.datetime(base.year, base.month, prev_day, base.hour, base.minute)
        return base
    
    def prev_run(self, time = datetime.datetime.now()):
        """Calculates when the previous execution was."""
        base = self.matches(time) and time or self.next_run(time)
        # minute
        prev_minute, carry = self.__prev_time(self.fields['minute'], base.minute)
        min_diff = datetime.timedelta(minutes=(base.minute - prev_minute))
        base -= min_diff
        if not carry :
            return base

        # hour
        prev_hour, carry = self.__prev_time(self.fields['hour'], base.hour)
        hour_diff = datetime.timedelta(hours=(base.hour - prev_hour))
        base -= hour_diff
        if not carry :
            return base

        # day and weekday are strongly depend on month and year

        prev_run = None
        completed = False
        prev_day, carry_day = self.__prev_time(self.fields['day'], base.day)
        _carry_day = False
        while 28 < prev_day and not _carry_day:
            date = self.__prev_date(base, prev_day, carry_day)
            if not prev_run or prev_run < date:
                prev_run = date
            _prev_day = prev_day
            prev_day, _carry_day = self.__prev_time(self.fields['day'], prev_day)
            carry_day = carry_day or _carry_day
        date = self.__prev_date(base, prev_day, carry_day)
        if not prev_run or prev_run < date:
            prev_run = date
            
        return prev_run
    
    def is_expired(self, time = datetime.datetime.now()):
        """If the expiration parameter has been set this will check
        wether too much time has been since the cron-entry. If the
        expiration has not been set, it throws ValueError."""
        if self.expiration == 0 :
            raise ValueError("Missing argument",
                             "Expiration time has not been set")
        next_beg = self.next_run(time)
        next_end = next_beg + self.expiration
        prev_beg = self.prev_run(time)
        prev_end = prev_beg + self.expiration
        if (time >= next_beg and time <= next_end) or (time >= prev_beg and time <= prev_end) :
            return False
        return True

def _test():
    import doctest
    doctest.testfile("cronTest.txt")

if __name__ == "__main__" :
    _test()
