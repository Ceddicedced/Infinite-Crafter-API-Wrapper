class Element:
    result: str
    emoji: str
    is_new: bool

    KEYS: list[str] = ["result", "emoji", "isNew"]

    def __init__(self, json: dict[str, str]):

        if not all(key in json for key in self.KEYS):
            raise ValueError("Invalid JSON - missing keys")

        self.result = json["result"]
        self.emoji = json["emoji"]
        self.is_new: bool = bool(json["isNew"])

    def __str__(self):
        return f"{self.emoji: <1}-{self.result}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Element):
            return False
        return self.result == other.result

    def __hash__(self) -> int:
        return hash(self.result)

    def __repr__(self) -> str:
        return f"Element({self.result!r}, {self.emoji!r}, {self.is_new!r})"

    def to_json(self) -> dict[str, str]:
        return {
            "result": self.result,
            "emoji": self.emoji,
            "isNew": str(self.is_new),
        }

    def to_args(self) -> tuple[str, str, bool]:
        return self.result, self.emoji, self.is_new

    @classmethod
    def from_json(cls, json: dict[str, str]) -> "Element":
        return cls(json)

    @classmethod
    def from_args(cls, result: str, emoji: str, is_new: bool) -> "Element":
        return cls({"result": result, "emoji": emoji, "isNew": str(is_new)})

    @property
    def json_bool(self) -> str:
        return str(self.is_new).lower()


BASE_ELEMENTS: set[Element] = {
    Element({"result": "Wind", "emoji": "🌬️", "isNew": "False"}),
    Element({"result": "Earth", "emoji": "🌍", "isNew": "False"}),
    Element({"result": "Fire", "emoji": "🔥", "isNew": "False"}),
    Element({"result": "Water", "emoji": "💧", "isNew": "False"}),
}

NOTHING_ELEMENT: Element = Element(
    {"result": "Nothing", "emoji": "🚫", "isNew": "False"}
)
ERROR_ELEMENT: Element = Element({"result": "Error", "emoji": "❌", "isNew": "False"})
