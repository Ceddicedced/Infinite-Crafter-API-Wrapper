import logging
from typing import Iterator
from element import Element, BASE_ELEMENTS
from storage import JSONStorage, AbstractStorage, SQLiteStorage
from requester import SyncRequester, AsyncRequester, AbstractRequester  # noqa: F401

logging.basicConfig(level=logging.INFO)

ALL_BASIC_ELEMENTS = 0
RANDOM_ELEMENTS_WITH_BASE = 1
RANDOM_WITH_RANDOM = 2


class Crafter:

    def __init__(self, requester: AbstractRequester, storage: AbstractStorage) -> None:
        self.requester = requester
        self.storage = storage
        self.storage.load()
        self.logger = logging.getLogger("Crafter")

    def craft(self, mode: int = 0, **kwargs: int) -> None:
        self.logger.info(f"Crafting with mode {mode}")
        match mode:
            case 0:
                self._all_basic_elements()
            case 1:
                count = kwargs.get("count", 5)
                self._random_elements_with_base(count=count)
            case 2:
                count = kwargs.get("count", 5)
                self._random_with_random(count=count)
            case _:
                self.logger.error(f"Invalid mode {mode}")
                raise ValueError("Invalid mode")

    def _get_random_elements(self, count: int) -> set[Element]:
        elements: set[Element] = self.storage.all_elements
        result: set[Element] = set()
        element_iter: Iterator[Element] = iter(elements)
        for _ in range(count):
            element = next(element_iter, None)
            if element is None:
                self.logger.warning("Not enough elements")
                break
            result.add(element)
        return result

    def _store_and_save_combinations(
        self, combinations: set[tuple[Element, Element]]
    ) -> set[Element]:
        for result in self.requester.generate_all(combinations):
            self.storage.store(result)
        new_elements = self.storage.new_elements
        self.storage.save()
        return new_elements

    def _all_basic_elements(self) -> None:
        elements = self.storage.load()
        self.logger.info(f"Combining {len(elements)} elements with all basic elements")
        while True:
            combinations: set[tuple[Element, Element]] = set()
            for element in elements:
                for element2 in BASE_ELEMENTS:
                    self.logger.debug(f"Combining {element} with {element2}")
                    combinations.add((element, element2))

            elements: set[Element] = self._store_and_save_combinations(combinations)
            if not elements:
                break

    def _random_elements_with_base(self, count: int = 5) -> None:
        self.logger.info(f"Combining {count} random elements with all basic elements")
        combinations: set[tuple[Element, Element]] = set()

        for element in self._get_random_elements(count):
            for base in BASE_ELEMENTS:
                combinations.add((element, base))

        self._store_and_save_combinations(combinations)

    def _random_with_random(self, count: int = 5) -> None:
        self.logger.info(
            f"Combining {count} random elements with {count} random elements"
        )
        combinations: set[tuple[Element, Element]] = set()

        random_set: set[Element] = self._get_random_elements(count * 2)

        for _ in range(count):
            combinations.add((random_set.pop(), random_set.pop()))

        self._store_and_save_combinations(combinations)

    def _specific_element_with_random(self, element1: Element, count: int = 5) -> None:
        self.logger.info(f"Combining {element1} with {count} random elements")
        combinations: set[tuple[Element, Element]] = set()

        for element2 in self._get_random_elements(count):
            combinations.add((element1, element2))

        self._store_and_save_combinations(combinations)

    def _specific_element_with_specific(
        self, element1: Element, element2: Element
    ) -> None:
        self.logger.info(f"Combining {element1} with {element2}")
        result = self.requester.get_element(element1, element2)
        self.storage.store(result)
        self.storage.save()


if __name__ == "__main__":

    logging.getLogger("AsyncRequester").setLevel(logging.DEBUG)
    # requester = SyncRequester()
    requester = AsyncRequester()
    # storage = JSONStorage("elements.json")
    storage = SQLiteStorage()
    crafter = Crafter(requester, storage)
    crafter.craft(mode=2, count=50)

    requester.close()
