"""
Browsers that allow you to do the actions in a way that is abstracted
"""
from selenium import webdriver
import os


class PreviewImageFound(Exception):
    """Raised when the image found is a preview image"""
    pass


class EndOfPageException(Exception):
    """Raised when you hit the end of a page of images"""
    pass


class Browser:
    """
    Each browser should have the following structure to be used by the scraper.
    It is intended to handle all the logic of clicking certain buttons and scraping links themselves.

    As google images updates its website, the xpath elements will change, so for each iteration
    of the browser subclass, make sure to label the date that it last worked at
    """

    def __init__(self, debug: list, **kwargs):
        raise NotImplementedError

    def get_website(self, url):
        raise NotImplementedError

    def click_first(self):
        raise NotImplementedError

    def click_next(self):
        raise NotImplementedError

    def get_image(self):
        raise NotImplementedError

    def get_related(self):
        raise NotImplementedError

    def end(self):
        raise NotImplementedError


import time


class DefaultBrowser(Browser):
    """
    Worked last in mid-july of 2021

    Debug flags: timeout - allows user to enter for timeout flags
    """

    def __init__(self, debug: list, **kwargs):

        # These are the xpaths to the elements that we will be interacting with
        self.arrowkey_xpath = "/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]/div[2]/c-wiz/div/div[" \
                              "1]/div[1]/div[1]/a[3]"
        self.first_img_xpath = "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div[1]/div[1]/span/div[1]/div[" \
                               "1]/div[1] "
        self.img_xpath = "/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[" \
                         "1]/div[2]/div[1]/a/img "
        self.related_xpath = "/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]/div[2]/c-wiz/div/div[" \
                             "1]/div[3]/div[3]/c-wiz/div/div/div[1]/div[2]/a "




        #os.chmod(kwargs['chromedriver_path'], 755)

        self.chromedriver_path = kwargs['chromedriver_path']
        self.timeout = kwargs['timeout']
        self.debug = debug
        self.kwargs = kwargs

        options = webdriver.ChromeOptions()
        for arg in kwargs['chromedriver_options']:
            options.add_argument(arg)
        self.browser = webdriver.Chrome(self.chromedriver_path, chrome_options=options)

    def get_website(self, url):
        self.browser.get(url)

    def click_first(self):
        initial_time = time.time()
        if 'click_first' in self.debug:
            print('click_first', "Trying to click first link")

        while True:

            if time.time() - initial_time > self.timeout:
                if 'click_first' in self.debug:
                    print('click_first', 'Timeout Error for first click')
                raise TimeoutError

            try:
                element = self.browser.find_elements_by_xpath(self.first_img_xpath)[0]
                element.click()
                break
            except Exception as e:
                if 'click_first' in self.debug:
                    print('click_first', e)

    def click_next(self):
        initial_time = time.time()
        if 'click_next' in self.debug:
            print('click_next', "Trying to click next button")

        while True:

            if time.time() - initial_time > self.timeout:
                if 'click_next' in self.debug:
                    print('click_next', 'Timeout Error for clicking next button')
                raise TimeoutError

            try:
                element = self.browser.find_elements_by_xpath(self.arrowkey_xpath)[0]
                # If this element is greyed out, then we are at the end of the page
                if element.get_attribute("aria-disabled") == 'true':
                    raise EndOfPageException("We have reached the end of the page")
                element.click()
                break
            # Accept indexerror in case the page hasnt loaded yet and the element hasnt loaded yet
            except IndexError as e:
                if 'click_next' in self.debug:
                    print('click_next', e)

    def get_image(self):
        initial_time = time.time()
        if 'get_image' in self.debug:
            print('get_image', "Trying to get the main image")

        while True:
            try:
                elem = self.browser.find_elements_by_xpath(self.img_xpath)[0]
                url = elem.get_attribute("src")
                if "data:image" in url or "encrypted-tbn0.gstatic.com" in url:
                    raise PreviewImageFound("We found a preview image as the primary link")
                break
            # Error and try again if a preview image is found
            except PreviewImageFound:
                if time.time() - initial_time > self.timeout:
                    break
                if 'get_image' in self.debug:
                    print('get_image', 'Found only preview image ' + url)
        return url

    def get_related(self):
        initial_time = time.time()
        if 'get_link' in self.debug:
            print("get_link", "Trying to get the main link")

        while True:

            if time.time() - initial_time > self.timeout:
                if 'get_link' in self.debug:
                    print('get_link', 'Couldnt find the related images link')
                raise TimeoutError

            try:
                element = self.browser.find_elements_by_xpath(self.related_xpath)[0]
                link = element.get_attribute('href')
                break
            # Accept an index error in the case that there is no related links thing to scrape or it just doesnt load
            except IndexError:
                pass

        return link

    def end(self):
        self.browser.close()
        self.browser.quit()
