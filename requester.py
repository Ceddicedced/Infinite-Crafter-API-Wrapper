import asyncio
import logging
from typing import Iterator, Optional, Set, Tuple
import requests
from element import Element, ERROR_ELEMENT
from abc import ABC, abstractmethod
import aiohttp


class AbstractRequester(ABC):
    BASE_URL: str = "https://neal.fun/api/infinite-craft/pair"
    HEADERS: dict[str, str] = {
        "authority": "neal.fun",
        "accept": "*/*",
        "accept-language": "de,en;q=0.9,en-US;q=0.8,en-GB;q=0.7,de-DE;q=0.6,es;q=0.5",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "referer": "https://neal.fun/infinite-craft/",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    @abstractmethod
    def get_element(self, element1: Element, element2: Element) -> Element:
        pass

    @abstractmethod
    def get_all(self, combinations: set[tuple[Element, Element]]) -> set[Element]:
        pass

    @abstractmethod
    def generate_all(
        self, combinations: set[tuple[Element, Element]]
    ) -> Iterator[Element]:
        pass

    @abstractmethod
    def close(self):
        pass


class SyncRequester(AbstractRequester):

    def __init__(self) -> None:
        self.headers = self.HEADERS
        self.url = "https://neal.fun/api/infinite-craft/pair"
        self.logger = logging.getLogger("Requester")
        self.session: Optional[requests.Session] = None

    def __del__(self):
        self.close()

    def close(self):
        if self.session is not None:
            self.session.close()

    def _create_session(self):
        if self.session is None:  # type: ignore
            self.session = requests.Session()

    def get(self, element1: str, element2: str) -> dict[str, str]:
        self._create_session()
        params: dict[str, str] = {
            "first": element1,
            "second": element2,
        }
        response = self.session.get(self.url, params=params, headers=self.headers)  # type: ignore
        log_str = f"GET {response.url} {params} https://http.cat/{response.status_code}"
        self.logger.debug(log_str)
        if response.status_code != 200:
            self.logger.error(log_str)
            return {"result": "Error", "emoji": "❌", "isNew": "False"}
        return response.json()

    def get_element(self, element1: Element, element2: Element) -> Element:
        json = self.get(element1.result, element2.result)
        result = Element(json)
        self.logger.info(f"Got {element1} + {element2} = {result}")
        return result

    def get_all(self, combinations: set[tuple[Element, Element]]) -> set[Element]:
        results: set[Element] = set()
        for element1, element2 in combinations:
            result = self.get_element(element1, element2)
            results.add(result)
        return results

    def generate_all(
        self, combinations: set[tuple[Element, Element]]
    ) -> Iterator[Element]:
        for element1, element2 in combinations:
            result = self.get_element(element1, element2)
            yield result


class AsyncRequester(AbstractRequester):
    def __init__(self) -> None:
        self.headers = AbstractRequester.HEADERS
        self.url = AbstractRequester.BASE_URL
        self.logger: logging.Logger = logging.getLogger("AsyncRequester")
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        # Initialize the session attribute without creating the session yet
        self.session: Optional[aiohttp.ClientSession] = None

    async def _create_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session is not None and not self.session.closed:
            await self.session.close()

    async def async_get(self, element1: str, element2: str) -> dict[str, str]:
        await self._create_session()  # Ensure the session is created and open
        params = {"first": element1, "second": element2}
        async with self.session.get(  # type: ignore
            self.url, params=params, headers=self.headers
        ) as response:
            log_str = f"GET {response.url} https://http.cat/{response.status}"
            self.logger.debug(log_str)
            if response.status != 200:
                self.logger.error(log_str)
                return ERROR_ELEMENT.to_json()
            return await response.json()

    def get_element(self, element1: Element, element2: Element) -> Element:
        json = self.loop.run_until_complete(
            self.async_get(element1.result, element2.result)
        )
        result = Element(json)
        self.logger.info(f"Got {element1} + {element2} = {result}")
        return result

    def get_all(self, combinations: Set[Tuple[Element, Element]]) -> Set[Element]:
        tasks = [
            self.async_get(element1.result, element2.result)
            for element1, element2 in combinations
        ]
        results: list[dict[str, str]] = self.loop.run_until_complete(
            asyncio.gather(*tasks)
        )
        return {Element(result) for result in results}

    def generate_all(
        self, combinations: Set[Tuple[Element, Element]]
    ) -> Iterator[Element]:
        tasks = [
            self.async_get(element1.result, element2.result)
            for element1, element2 in combinations
        ]
        results = self.loop.run_until_complete(asyncio.gather(*tasks))
        for result in results:
            yield Element(result)

    def close(self):
        if self.loop.is_running():
            asyncio.ensure_future(self.close_session())
        else:
            self.loop.run_until_complete(self.close_session())

    def __del__(self):
        # Attempt to close the session when the object is deleted
        # Note: This is not reliable for async cleanup; consider explicit cleanup instead.
        if self.loop.is_running():
            asyncio.ensure_future(self.close_session())
        else:
            self.loop.run_until_complete(self.close_session())
