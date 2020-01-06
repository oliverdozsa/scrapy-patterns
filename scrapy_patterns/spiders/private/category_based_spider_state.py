"""This is a private module containing state handling for category based spider."""
import os
import json
import logging
from typing import Optional
from scrapy_patterns.site_structure import SiteStructure


# pylint: disable=too-many-instance-attributes
class CategoryBasedSpiderState:
    """The class holding the state."""
    def __init__(self, spider_name: str, progress_file_dir: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.site_structure: Optional[SiteStructure] = None
        self.current_page_url = None
        self.current_page_site_path = None
        self.is_loaded = False
        self.__spider_name = spider_name
        self.__progress_file_dir = progress_file_dir
        self.__json_file_path = os.path.join(progress_file_dir, spider_name + "_progress.json")

        if self.__does_file_exist():
            self.__load()
            self.logger.info("[%s] State loaded from file: %s", self.__spider_name, self.__json_file_path)
            self.log()
            self.is_loaded = True

    def save(self):
        """Saves the state to the progress file."""
        if self.site_structure is None:
            raise RuntimeError("[%s] Site structure doesn't exist!" % self.__spider_name)
        self.logger.info("[%s] Saving state.", self.__spider_name)
        if not os.path.isdir(self.__progress_file_dir):
            os.mkdir(self.__progress_file_dir)
        with open(self.__json_file_path, "w") as json_file:
            json_state = {
                "site_structure": self.site_structure.to_dict(),
                "current_page_url": self.current_page_url,
                "current_page_site_path": self.current_page_site_path
            }

            json.dump(json_state, json_file)

    def log(self):
        """Logs the state."""
        self.logger.info("[%s] state:\n"
                         "current_page_url = %s\n"
                         "current_page_site_path = %s\n"
                         "site_structure =\n%s",
                         self.__spider_name, self.current_page_url, self.current_page_site_path,
                         str(self.site_structure))

    def __does_file_exist(self):
        return os.path.isfile(self.__json_file_path)

    def __load(self):
        with open(self.__json_file_path, "r") as json_file:
            json_state = json.load(json_file)
            self.site_structure = SiteStructure.from_dict(json_state["site_structure"])
            self.current_page_url = json_state["current_page_url"]
            self.current_page_site_path = json_state["current_page_site_path"]
