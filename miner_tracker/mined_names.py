import csv
import difflib
import re
from dataclasses import dataclass

from config import config


@dataclass
class MarketName:
    category: str
    trade_name: str
    id: int
    symbol: str


class Commodities:
    """Fuzzy namer class, game logs have bugs in naming mined commodity +
    user may enter whatever, this class helps to find exact name by catalogue.
    """

    # Data based on on commodities dictionary file, created and maintained by the community.
    # Building data 1 time on 1st use.
    _SYMBOL_TO_MARKET_NAMES: dict[str, MarketName] = {}  # noqa: RUF012
    _CANDIDATES: list[tuple[str, MarketName]] = []  # noqa: RUF012
    _SEARCH_STRINGS: list[str] = []  # noqa: RUF012
    _LOADED: bool = False

    _TEMPLATE_PATTERN = re.compile(r"^\$(\w+)_name;$")

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._LOADED:
            cls.load_commodity_map()
            cls._LOADED = True

    @classmethod
    def load_commodity_map(cls) -> None:
        # Mined resources are not rares, so we don't load rares list.
        for f in "commodity.csv":
            if not (config.app_dir_path / "FDevIDs" / f).is_file():
                continue
            with open(
                config.app_dir_path / "FDevIDs" / f, "r", encoding="utf-8"
            ) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    symbol_lower = row["symbol"].strip().lower()
                    cls._SYMBOL_TO_MARKET_NAMES[symbol_lower] = MarketName(
                        category=row["category"].strip(),
                        trade_name=row["name"].strip(),
                        id=int(row["id"]),
                        symbol=symbol_lower,
                    )
        if len(cls._SYMBOL_TO_MARKET_NAMES) < 5:
            raise RuntimeError("Could not load commodities.")

        for m in cls._SYMBOL_TO_MARKET_NAMES.values():
            cls._CANDIDATES.append((m.symbol, m))
            cls._CANDIDATES.append((m.trade_name.lower(), m))

        cls._SEARCH_STRINGS = [c[0] for c in cls._CANDIDATES]

    @classmethod
    def resolve(cls, raw_input: str) -> MarketName | None:
        """Fuzzy name validation with Prefix support."""
        cls._ensure_loaded()
        clean_input = raw_input.strip()
        template_match = cls._TEMPLATE_PATTERN.match(clean_input)

        if template_match:
            search_term = template_match.group(1).lower()
        else:
            search_term = clean_input.lower()

        if search_term in cls._SYMBOL_TO_MARKET_NAMES:
            return cls._SYMBOL_TO_MARKET_NAMES[search_term]

        for text, m_obj in cls._CANDIDATES:
            if text.startswith(search_term):
                return m_obj

        matches = difflib.get_close_matches(
            search_term,
            cls._SEARCH_STRINGS,
            n=1,
            cutoff=0.6,
        )

        if matches:
            matched_str = matches[0]
            for text, m_obj in cls._CANDIDATES:
                if text == matched_str:
                    return m_obj

        return None

    @classmethod
    def resolve_db_value(cls, raw_input: str | None) -> str | None:
        if not raw_input:
            return None

        resolved = cls.resolve(raw_input=raw_input)
        if resolved:
            return resolved.symbol
        return None
