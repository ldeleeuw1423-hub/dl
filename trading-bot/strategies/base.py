"""Abstract base class for all trading strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional

import pandas as pd

Direction = Literal["long", "short", "flat"]


@dataclass
class Signal:
    direction: Direction      # "long", "short", or "flat"
    confidence: float         # 0.0 – 1.0
    reason: str               # human-readable explanation
    instrument: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    size_multiplier: float = 1.0   # sentiment overlay adjusts this


class Strategy(ABC):
    """All strategies implement generate_signal()."""

    name: str = "base"

    @abstractmethod
    def generate_signal(
        self,
        df: pd.DataFrame,           # OHLCV with indicators already applied
        instrument: str,
        **kwargs,
    ) -> Signal:
        """Analyse df and return a Signal."""
        ...

    def __repr__(self) -> str:
        return f"<Strategy {self.name}>"
