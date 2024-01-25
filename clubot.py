# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime
from email.mime.text import MIMEText
from operator import attrgetter
from pathlib import Path
from time import sleep
from bs4 import BeautifulSoup
import json
import webbrowser
import pandas as pd
import requests
import smtplib
import yaml


CLUB_AGENDA = "https://www.clubalpinlyon.fr/agenda"
""" Base URL for the club agenda page. """

QUERY = "month={m}&year={Y}"
""" Expected query format for pagination. """


def get_starting_date():
    """ Get year/month for starting query.
    
    Reference: https://stackoverflow.com/questions/61792422
    """
    # This is simpler, though less elegant.
    # year, month = tuple(date.today().timetuple())[:2]
    year, month = attrgetter("year", "month")(date.today())
    return year, month


def get_requested_soup(url):
    """ Wrap requesting a page and converting to soup.
    
    Note: because <tr> tags are not closed in agenda, default HTML
    parser will not work and `html5lib` is required.
    """
    page = requests.get(url)

    match page.status_code:
        case 200:
            soup = BeautifulSoup(page.text, "html5lib")
        case _:
            soup = None
        
    return soup


def get_agenda_from_url(url):
    """ Get agenda table from soup through `find` method. """
    soup = get_requested_soup(url)
    agenda = soup.find(id="main").find(id="left1").find(id="agenda")
    return agenda


def get_timestamp():
    """ Get formatted text timestamp for database. """
    return datetime.now().strftime(r"%Y-%m-%dT%H-%M-%S")


def load_database(data_file):
    """ Load activity database from file. """
    if not Path(data_file).exists():
        return {}
    
    with open(data_file, encoding="utf-8") as fp:
        data = json.load(fp)

    return data


def process_row(db, row, new_events):
    """ Process a data row for adding/modifying database. """
    row_date = row.find(class_="agenda-gauche").text
    row_evns = [" ".join(r.text.split()) for r in row.find_all("h2")]

    # Consider date could be in database but now we don't find any
    # events, meaning they were manually deleted by some admin.
    if row_date in db and not row_evns:
        print(f"Events from {row_date} were suppressed!")

        # Do not remove them from database, but instead tag as deleted
        # so that we can know when things go missing!
        events = db[row_date]
        for event_no, event in enumerate(events):
            event = f"DELETED: {event}"
            db[row_date][event_no] = event

    # Otherwise if there is nothing on current row, continue.
    if not row_evns:
        return

    # If this date was not present, then all events are new and
    # we have nothing else to do here.
    if row_date not in db:
        print(f"New events added to {row_date}")
        db[row_date] = []

        for event in row_evns:
            new_events.append({"date": row_date, "title": event})

        return

    # If date already existed, so we need to check if nothing
    # new was added or modified here.
    if "events" in db[row_date]:
        for event in row_evns:
            existing = [e["title"] for e in db[row_date]]

            if event not in existing:
                new_events.append({"date": row_date, "title": event})

        for event in db[row_date]:
            if event["title"] not in row_evns:
                print(f"An event from {row_date} was suppressed!")
                print(event)
                # TODO find index here!


def feed_activity(activity, data_file, html_file):
    """ """
    # Load or create database.
    db = load_database(data_file)

    # Assume there are no new events at this call time.
    new_events = []
    
    # Start from current month, for this year.
    year, month = get_starting_date()

    # Tag all entries with current starting time.
    added_time = get_timestamp()
    print(f"\n*** New call at {added_time}: {activity}")

    for m in range(month, 12+1):
        # Use a string for representing the month.
        this_month = str(m)

        # Form URL for performing request.
        url = activity.format(m=this_month, Y=year)

        # Retrieve all table rows from agenda.
        entries = get_agenda_from_url(url).find_all("tr")

        # Append montly data to database.
        for row in entries:
            process_row(db, row, new_events)

    for entry in new_events:
        edate, etitle = entry["date"], entry["title"]
        db[edate].append({"timestamp": added_time, "title": etitle})
    
    # TODO email if new_events is not empty!
    with open(data_file, "w", encoding="utf-8") as fp:
        json.dump(db, fp)

    # Generate HTML file for visualisation.
    df = pd.DataFrame([{"date": edate, **event}
                       for edate, events in db.items()
                       for event in events])
    
    # with open(html_file, "w") as fp:
    #     fp.write(df.to_html())

    return new_events


def observer(open_browser, activities):
    """ Main program observer loop. """
    here = Path(__file__).resolve().parent

    dumps = here / "dumps"
    dumps.mkdir(exist_ok=True)

    for name in activities:
        activity = f"{CLUB_AGENDA}/{name}.html?{QUERY}"
        data_file = dumps / f"{name}.json"
        html_file = dumps / f"{name}.html"
        new_events = feed_activity(activity, data_file, html_file)

        # if new_events:
        #     beepy.beep(sound="ping")

        if new_events and open_browser:
            webbrowser.open(f"file://{here.as_posix()}/{html_file}")
        

class Clubot:
    def __init__(self,
        config: str | Path = "clubot.yaml",
        period: int = 600,
        browse: bool = False
    ):
        with open(config) as fp:
            data = yaml.safe_load(fp)

        self.activities = data["activities"]
        




if __name__ == "__main__":
    repeat_every = 600
    open_browser = False

    bot = Clubot()

    while True:
        observer(open_browser, bot.activities)
        sleep(repeat_every)
