from datetime import datetime, timedelta

CAR2GO_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'  # %Y = e.g. 2014, %y = 14!!!


def timediff_seconds(first: datetime, second: str):
    try:
        second_datetime = datetime.strptime(second, CAR2GO_DATETIME_FORMAT)
    except ValueError as e:
        raise RuntimeError(
            f"Could not convert '{second}' to datetime obj with format '{CAR2GO_DATETIME_FORMAT}'"
            f"{e}")
    time_diff = second_datetime - first
    return abs(time_diff.total_seconds())


def to_car2go_format(dt: datetime):
    return dt.strftime(format=CAR2GO_DATETIME_FORMAT)


def from_car2go_format(dt: str):
    return datetime.strptime(dt, CAR2GO_DATETIME_FORMAT)