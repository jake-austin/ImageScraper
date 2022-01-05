"""
This is the database that will be used for the pools of queued tasts, in progress tasks, and
completed tasks.

Any custom versions of this class will be independently responsible for handling
requests in a way that can be done concurrently between multiple threads

Any custom versions of these classes should be able to persist independently of pythonic
variable references... meaning it is intended to be called once to create the database,
and all previous instantiations with the same arguments just open the old database object.
This can be achieved with a database file that you make in the first instantiation and read
from with all other instantiations with the same args

The reason for all this stuff about being able to recover the databases is in the case of
early stopping of a search, making sure we can pick up where we left off without loss or wasted time

If your database is remote and can handle requests from different
processes on different machines, then you can make this work with a small army of
aws spot instances even


Basic Database Idea:

          / \
        /    \
      <       \
Queue --> InProgress --> Completed --> Downloaded
"""
import pathlib


class Database:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    # adds shit to the queue
    def add_queue(self, url, folder_name, controller_kwargs):
        raise NotImplementedError

    # adds lots of shit to the queue from a list of tuples
    def addmany_queue(self, data: list):
        raise NotImplementedError

    # gets a task and moves it to in-progress
    def get_task(self):
        raise NotImplementedError

    # finished a scrub with url request
    def completed_task(self, url, links_scraped, folder_name):
        raise NotImplementedError

    # moves a task to downloaded
    def downloaded_url(self, url):
        raise NotImplementedError

    def check_done(self):
        raise NotImplementedError

    def get_download_link(self):
        raise NotImplementedError


import sqlite3
import json


class DefaultDatabase(Database):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fp = './database.db'
        exists = pathlib.Path(self.fp).exists()

        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        # Create tables
        if not exists:
            cur.execute('''CREATE TABLE queue 
                           (url text, folder_name text, controller_kwargs text)''')
            cur.execute('''CREATE TABLE in_progress 
                           (url text, folder_name text, controller_kwargs text)''')
            cur.execute('''CREATE TABLE completed 
                        (img_url text, source text, folder_name text)''')
            cur.execute('''CREATE TABLE downloaded 
                        (img_url text, source text, folder_name text)''')
        # Close tables for the time being
        con.commit()
        con.close()

    def add_queue(self, url, folder_name, controller_kwargs):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("INSERT INTO queue (url, folder_name, controller_kwargs) "
                    "VALUES ((?), (?), (?))", (url, folder_name, json.dumps(controller_kwargs)))
        con.commit()
        con.close()

    def addmany_queue(self, data: list, folder_name: str):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        for url, controller_kwargs in data:
            cur.execute("INSERT INTO queue (url, folder_name, controller_kwargs) "
                        "VALUES ((?), (?), (?))", (url, folder_name, json.dumps(controller_kwargs)))
        con.commit()
        con.close()

    def get_task(self):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("""SELECT * FROM queue""")
        row = list(cur.fetchone())
        cur.execute("DELETE FROM queue WHERE url LIKE (?)", (row[0],))
        cur.execute("INSERT INTO in_progress (url, folder_name, controller_kwargs) "
                    "VALUES ((?), (?), (?))", (row[0], row[1], row[2]))
        con.commit()
        con.close()

        row[2] = json.loads(row[2])
        return row

    # finished a scrub with url request
    def completed_task(self, url: str, links_scraped: list, folder_name: str):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("""DELETE FROM in_progress WHERE url LIKE (?)""", (url,))
        for link in links_scraped:
            cur.execute("INSERT INTO completed (img_url, source, folder_name) "
                        "VALUES ((?), (?), (?))", (link, url, folder_name))
        con.commit()
        con.close()

    # moves a task to downloaded
    def downloaded_url(self, img_url):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("""SELECT * FROM completed WHERE img_url LIKE (?)""", (img_url,))
        row = cur.fetchone()
        cur.execute("""DELETE FROM completed WHERE img_url LIKE (?)""", (img_url,))
        cur.execute("INSERT INTO downloaded (img_url, source, folder_name) "
                    "VALUES ((?), (?), (?))", (row[0], row[1], row[2]))
        con.commit()
        con.close()

    def queue_or_in_progress_contains(self, url):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("SELECT * FROM queue WHERE img_url LIKE (?)", (url,))
        queue = cur.fetchone()
        cur.execute("SELECT * FROM in_progress WHERE img_url LIKE (?)", (url,))
        in_progress = cur.fetchone()
        con.close()

        return bool(queue) or bool(in_progress)

    def completed_or_download_contains(self, img_url):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("SELECT * FROM completed WHERE img_url LIKE (?)", (img_url,))
        completed = cur.fetchone()
        cur.execute("SELECT * FROM downloaded WHERE img_url LIKE (?)", (img_url,))
        downloaded = cur.fetchone()
        con.close()

        return bool(completed) or bool(downloaded)

    def check_done(self):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("""SELECT * FROM queue""")
        queue = cur.fetchone()
        cur.execute("""SELECT * FROM in_progress""")
        in_progress = cur.fetchone()
        con.close()

        return not (bool(queue) or bool(in_progress))

    def get_download_link(self):
        con = sqlite3.connect(self.fp)
        cur = con.cursor()
        cur.execute("""SELECT * FROM completed""")
        img_url, source, folder_name = cur.fetchone()
        return img_url
