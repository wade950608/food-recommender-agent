from typing import Literal

from pydantic import BaseModel, Field

PriceRange = Literal["$ 平價(150元以下)", "$$ 中等(150-400元)", "$$$ 高價(400元以上)"]


class FoodOption(BaseModel):
    dish: str = Field(description="餐點名稱")
    cuisine_style: str = Field(description="菜系或風格，例如台式、日式")
    price_range: PriceRange
    reason: str = Field(description="為什麼適合現在的心情，一句話")


class DecisionReport(BaseModel):
    mood_analysis: str = Field(description="對使用者心情與需求的簡短分析")
    options: list[FoodOption] = Field(description="剛好 3 個候選")
    final_verdict: str = Field(description="一句話最終決策")


SYSTEM = (
    "你是「吃什麼決策小幫手」。依使用者的心情、預算或想法，用繁體中文輸出："
    "心情分析、剛好 3 個候選餐點（以台灣常見餐點為主，價位須符合預算）、"
    "以及一句話的最終決策。價位區間只能從固定選項中選。"
)
