 def get_date(self):
        date = datetime.date.today()
        date_str = str(date.year)
        if len(str(date.month)) <= 1:
            date_str = date_str + '0' + str(date.month)
        else:
            date_str = date_str + str(date.month)
        if len(str(date.day)) <= 1:
            date_str = date_str + '0' + str(date.day)
        else:
            date_str = date_str + str(date.day)
        return date_str