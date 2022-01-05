"""
It is intended that nothing in this file changes. You can modify the behavior of this by adding your
own subclasses to other areas and selecting them in the config
"""
import pathlib
import time
from multiprocessing import Pool
from multiprocessing import Semaphore
from multiprocessing import Process
from tqdm import tqdm

from config import DATABASE
from config import DATABASE_KWARGS
from config import MAIN_ARGS
from config import BROWSER
from config import BROWSER_KWARGS
from config import DEBUG
from config import DOWNLOAD
from config import JOB_FAIL_LIMIT
from config import END_ON_JOB_FAIL
from config import RECURSIVE_FAIL_FRACTION_LIMIT
from config import CONTROLLER
from config import WORKERS
from config import RESUME


def estimate_links(controller_class, init_kwargs, verbose=0):
    """
    Used to ballpark the number of images we will be checking.
    Used for tqdm progressbar, and for testing your config
    """
    count = 0
    recursive = [init_kwargs]

    while recursive:
        controller = controller_class(**recursive.pop())
        for kwargs in controller:
            if kwargs:
                recursive.append(kwargs)
            count += 1
        if verbose and count % verbose:
            print(count)
    return count


from scraper.browser import EndOfPageException


def scrub(url, controller, browser, recursive_fail_limit):
    """
    The actual scrubber. Simple once the browser/controller is working.
    recursive_fail_limit is a number of times we aren't allowed to
    """
    links = []
    recursive_links = []
    recursive_fails = 0

    # try and load the page
    browser.get_website(url)

    # trys to click on the first image
    browser.click_first()

    for kwargs in controller:
        # attempts to get the picture from the element, tries again if it maybe hasnt loaded yet
        url = browser.get_image()
        links.append(url)

        # adds the link to the list, gets the related link if there is a recursive call (kwargs is None otherwise)
        related = None
        try:
            related = browser.get_related()
        except TimeoutError:
            recursive_fails += 1
            if recursive_fails > recursive_fail_limit:
                raise TimeoutError

        # If we have reached the end of the page, then there is nothing more that we can do here
        try:
            browser.click_next()
        except EndOfPageException:
            break

        if kwargs and related:
            recursive_links.append([related, kwargs])

    return links, recursive_links


def job(semaphore, task, database):
    browser = BROWSER(debug=DEBUG, **BROWSER_KWARGS)
    semaphore.acquire()
    for attempt in range(JOB_FAIL_LIMIT):
        try:
            url, folder_name, kwargs = task
            controller = CONTROLLER(**kwargs)
            links, recursive_links = scrub(url, controller, browser, RECURSIVE_FAIL_FRACTION_LIMIT * len(controller))
            break
        # In the case of ANY exception failing a job, we want to keep trucking on and try again
        except Exception as e:
            print('Job failed at url ' + url, e)
            if attempt + 1 == JOB_FAIL_LIMIT:
                raise e
    browser.end()
    database.completed_task(url, links, folder_name)
    database.addmany_queue(recursive_links, folder_name)
    semaphore.release()


def get_url_from_terms(search_phrase: str):
    # This should be a good way to search from a term
    return "https://www.google.co.in/search?q=" + search_phrase + "&source=lnms&tbm=isch"


if __name__ == "__main__":

    # starts setting up the download directory structure
    pathlib.Path("downloads").mkdir(exist_ok=True)

    # creates the databse object... all initialization done here
    database = DATABASE(**DATABASE_KWARGS)

    # Sets up all the initial queueing if we aren't just resuming
    folder_names = []
    for search in MAIN_ARGS:
        folder_name = str(search[0]).strip("'[]")[:64]
        folder_names.append(folder_name)
        if not RESUME:
            for term in search[0]:
                database.add_queue(get_url_from_terms(term), folder_name, search[1])

    errors = []
    count = 0

    sema = Semaphore(WORKERS)

    # All the actual work is done here, blocked by semaphores
    while not database.check_done():
        task = database.get_task()

        if task:
            try:
                p = Process(target=job, args=(sema, task, database))
                p.start()
                p.join()
            # In the case of ANY job failure, we want to keep trucking onto other processes, unless specified
            except Exception as e:
                print("Job failed totally at url " + task[0], e)
                if END_ON_JOB_FAIL:
                    raise e

        else:
            time.sleep(5)

    if DOWNLOAD:
        DOWNLOAD(folder_names, database, )
