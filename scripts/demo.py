import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Product, Stage, InputShare
from src.database import select_all


def main():
    products: list[Product] = select_all(Product)
    stages: list[Stage] = select_all(Stage)
    input_shares: list[InputShare] = select_all(InputShare)

    print("Products:")
    for product in products:
        print(f"  {product.name} ({product.brand})")

    print("\nStages:")
    for stage in stages:
        print(f"  {stage.stage_type} - {stage.location_country}")

    print("\nInput Shares:")
    for share in input_shares:
        print(f"  {share.input_name}: {share.percentage}%")


if __name__ == "__main__":
    main()

