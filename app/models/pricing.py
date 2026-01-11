"""
模型定价信息 (借鉴 Dify PriceConfig)

支持多货币和成本估算。
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ModelPricing:
    """模型定价信息"""

    input: Decimal
    output: Decimal
    unit: Decimal = Decimal("0.000001")  # 默认 per 1M tokens
    currency: str = "USD"

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """估算单次调用成本"""
        return (
            Decimal(input_tokens) * self.input + Decimal(output_tokens) * self.output
        ) * self.unit

    @classmethod
    def from_per_million(
        cls, input_per_m: float, output_per_m: float, currency: str = "USD"
    ) -> "ModelPricing":
        """从 per 1M tokens 价格创建"""
        return cls(
            input=Decimal(str(input_per_m)),
            output=Decimal(str(output_per_m)),
            unit=Decimal("0.000001"),
            currency=currency,
        )
