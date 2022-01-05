"""
This is a file that allows for some customization of the scraper... allowing custom things to be
built. All you need to do is add your own modules to the scraper folder and import them here
so they will be used in the scraper
"""


"""
MAIN_ARGS:
Should be a list of tuples representing classes that you want to add
Each class can have multiple independent searches
Each class's tuple contains [0] a list of search terms and [1] a dictionary of Controller kwargs
"""
CONTROLLER_KWARGS = {'depth': 2,
                     'original_number': 300,
                     'original_depth': 2,
                     'scaling_factor': .5}
MAIN_ARGS = [(["crow", "raven"], CONTROLLER_KWARGS),
             (["fruit basket", "fruit bundle"], CONTROLLER_KWARGS),
             (["coffee table", "small table"], CONTROLLER_KWARGS),
             (["potted plant", "small plants"], CONTROLLER_KWARGS),
             (["chairs", "living room chairs"], CONTROLLER_KWARGS),
             (["lamp", "living room lighting"], CONTROLLER_KWARGS)]
WORKERS = 1                                 # Number of browser instances that we will juggle
RESUME = False                              # Whether this is a fresh start or this is a job that we are resuming
DOWNLOAD = False                            # Whether or not to download
DEBUG = []#['click_first', 'click_next', 'get_image', 'get_link']     # A list of shit that we can choose debugging for
DRIVER_PATH = './drivers/chromedriver'      # Path to the chromdriver file
TIMEOUT_LENGTH = 2                          # A timeout for website loading, after which we will fail that process
JOB_FAIL_LIMIT = 5                          # The number of times that any scrub is able to fail before we error
END_ON_JOB_FAIL = False                     # Whether or not we want to exit the program when a job fails
RECURSIVE_FAIL_FRACTION_LIMIT = 1           # The number of times that we can timeout on finding recursive links


"""
CONTROLLER
Imports a controller from the scraper.control file
"""
from scraper.control import DefaultController

CONTROLLER = DefaultController


"""
BROWSER
Imports the browser subclass that we will be using
Also defines the arguments for that browser that we will be using
"""
from scraper.browser import DefaultBrowser

BROWSER_KWARGS = {'chromedriver_path': DRIVER_PATH,
                  'chromedriver_options': [#'--headless',
                                           '--disable-gpu',
                                           '--ignore-ssl-errors',
                                           '--ignore-certificate-errors',
                                           "--window-size=800,600"],
                  'timeout': TIMEOUT_LENGTH}
BROWSER = DefaultBrowser


"""
DATABASES
Imports a Queue database solution for queued searches, sets the class that we will use
Imports a Completed database solution for completed searches, sets the class that we will use
"""
from scraper.database import DefaultDatabase
DATABASE = DefaultDatabase
DATABASE_KWARGS = {}


"""
DOWNLOADER
This is the downloader program that gets us from the completed databases to our downloads

from downloader import download
if DOWNLOAD:
    DOWNLOAD = download
else:
    DOWNLOAD = None
"""