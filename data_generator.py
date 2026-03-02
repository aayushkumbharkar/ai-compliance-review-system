import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

NUM_USERS = 1000
TX_PER_USER = 100

COUNTRIES = ["Canada", "USA", "UK"]
MERCHANT_CATEGORIES = ["grocery", "electronics", "travel", "restaurant"]
DEVICES = ["mobile", "web", "tablet"]

def generate_synthetic_data():
    np.random.seed(42)
    random.seed(42)

    all_transactions = []

    start_date = datetime.now() - timedelta(days=30)

    for user_id in range(NUM_USERS):
        base_country = random.choice(COUNTRIES)
        base_device = random.choice(DEVICES)

        # Normal behavior baseline
        avg_amount = np.random.uniform(20, 200)
        std_amount = avg_amount * 0.3

        last_time = start_date

        for tx_id in range(TX_PER_USER):
            timestamp = last_time + timedelta(
                minutes=np.random.randint(10, 1440)
            )
            last_time = timestamp

            amount = max(1, np.random.normal(avg_amount, std_amount))
            merchant = random.choice(MERCHANT_CATEGORIES)

            transaction = {
                "user_id": user_id,
                "transaction_id": f"{user_id}_{tx_id}",
                "timestamp": timestamp,
                "amount": round(amount, 2),
                "country": base_country,
                "device_id": base_device,
                "merchant_category": merchant,
                "is_anomaly": 0
            }

            all_transactions.append(transaction)

        # Inject anomalies for 5% of users
        if random.random() < 0.05:
            anomaly_type = random.choice(
                ["amount_spike", "country_change", "burst_activity"]
            )

            if anomaly_type == "amount_spike":
                all_transactions[-1]["amount"] *= 5
                all_transactions[-1]["is_anomaly"] = 1

            elif anomaly_type == "country_change":
                all_transactions[-1]["country"] = "Russia"
                all_transactions[-1]["is_anomaly"] = 1

            elif anomaly_type == "burst_activity":
                burst_time = last_time
                for i in range(5):
                    burst_tx = {
                        "user_id": user_id,
                        "transaction_id": f"{user_id}_burst_{i}",
                        "timestamp": burst_time + timedelta(minutes=i),
                        "amount": round(np.random.uniform(100, 500), 2),
                        "country": base_country,
                        "device_id": base_device,
                        "merchant_category": "electronics",
                        "is_anomaly": 1
                    }
                    all_transactions.append(burst_tx)

    df = pd.DataFrame(all_transactions)

    return df

if __name__ == "__main__":
    df = generate_synthetic_data()
    print("Dataset generated successfully.")
    print(df.head())
    print("\nTotal transactions:", len(df))
    print("Total anomalies:", df["is_anomaly"].sum())