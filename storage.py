import sqlite3
from typing import Set
import jsonpickle  # type: ignore
import logging
from element import Element
from abc import ABC, abstractmethod


class AbstractStorage(ABC):

    file: str
    loaded_elements: set[Element]
    non_loaded_elements: set[Element]
    logger: logging.Logger

    def __init__(self, name: str) -> None:
        self.loaded_elements: set[Element] = set()
        self.non_loaded_elements: set[Element] = set()
        self.logger = logging.getLogger(name)

    @abstractmethod
    def load(self) -> set[Element]:
        pass

    @abstractmethod
    def save(self) -> None:
        pass

    def store(self, element: Element) -> None:
        if element not in self.loaded_elements:
            self.logger.debug(f"Storing new element {element}")
            self.non_loaded_elements.add(element)
        else:
            self.logger.debug(f"Element {element} already stored")

    def pprint(self) -> None:
        out = "Storage:\n"
        for element in self.loaded_elements:
            out += f"\t {element}\n"
        print(out)

    @property
    def new_elements(self) -> set[Element]:
        return self.non_loaded_elements

    @property
    def all_elements(self) -> set[Element]:
        return self.loaded_elements

    def __repr__(self) -> str:
        return f"Storage({self.file!r})"

    def __str__(self) -> str:
        return f"Storage with {len(self.loaded_elements)} elements"

    def to_chrome_storage(self) -> str:
        # Chrome -> App -> Storage -> Local Storage -> https://neal.fun/infinite-craft/ -> key: infinite-craft-data
        out = '{"elements": ['
        for element in self.loaded_elements:
            out += (
                "{"
                + f'"text": "{element.result}", "emoji": "{element.emoji}", "discovered": {element.json_bool}'
                + "},"
            )
        out = out[:-1] + "]}"
        return out


class JSONStorage(AbstractStorage):
    EMPTY_JSON = '{"py/set": []}'

    def __init__(self, file: str = "elements.json") -> None:
        super().__init__("JSONStorage")
        self.file = file

    def _read(self) -> str:
        try:
            with open(self.file, "r") as file:
                self.logger.debug(f"Reading from {self.file}")
                return file.read()
        except FileNotFoundError:
            self.logger.debug(f"File {self.file} not found")

            try:
                with open(self.file, "w") as file:
                    self.logger.debug(f"Creating file {self.file}")
                    file.write(self.EMPTY_JSON)
            except FileNotFoundError:
                self.logger.error(f"Could not create file {self.file}")
            finally:
                return self.EMPTY_JSON

    def _write(self, data: str) -> None:
        with open(self.file, "w") as file:
            self.logger.debug(f"Writing to {self.file}")
            file.write(data)

    def load(self) -> set[Element]:
        self.loaded_elements = jsonpickle.decode(self._read())  # type: ignore
        self.logger.info(f"Loaded {len(self.loaded_elements)} elements")  # type: ignore
        self.non_loaded_elements = set()
        return self.loaded_elements  # type: ignore

    def save(self) -> None:
        self.loaded_elements.update(self.non_loaded_elements)
        self._write(jsonpickle.encode(self.loaded_elements))  # type: ignore
        self.logger.info(f"Saved {len(self.loaded_elements)} elements")
        self.non_loaded_elements = set()


class SQLiteStorage(AbstractStorage):
    def __init__(self, db_file: str = "elements.sqlite3") -> None:
        super().__init__("SQLiteStorage")
        self.db_file = db_file
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS elements (
                    result TEXT PRIMARY KEY,
                    emoji TEXT NOT NULL,
                    is_new BOOLEAN NOT NULL
                )
            """
            )
            conn.commit()

    def load(self) -> Set[Element]:
        with sqlite3.connect(self.db_file) as conn:
            self.logger.debug(f"Loading from {self.db_file}")
            cursor = conn.cursor()
            cursor.execute("SELECT result, emoji, is_new FROM elements")
            rows = cursor.fetchall()
            self.loaded_elements = set(Element.from_args(*row) for row in rows)
            self.non_loaded_elements = set()
            self.logger.info(f"Loaded {len(self.loaded_elements)} elements")
        return self.loaded_elements

    def save(self) -> None:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            for element in self.non_loaded_elements:
                args = element.to_args()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO elements (result, emoji, is_new)
                    VALUES (?, ?, ?)
                """,
                    args,
                )
            conn.commit()
            self.logger.info(f"Saved {len(self.non_loaded_elements)} elements")
        self.loaded_elements.update(self.non_loaded_elements)
        self.non_loaded_elements = set()
