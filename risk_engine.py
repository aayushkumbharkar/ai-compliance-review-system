import pandas as pd
import numpy as np

def compute_user_baseline(df):
    """
    Precompute per-user statistics.
    """
    user_stats = df.groupby("user_id").agg(
        avg_amount=("amount", "mean"),
        std_amount=("amount", "std"),
        most_common_country=("country", lambda x: x.mode()[0]),
        most_common_device=("device_id", lambda x: x.mode()[0])
    ).reset_index()

    return user_stats


def compute_risk(transaction, user_stats, user_history):
    """
    Compute deterministic risk metrics for one transaction.
    """

    user_id = transaction["user_id"]
    stats = user_stats[user_stats["user_id"] == user_id].iloc[0]

    # 1️⃣ Amount Z-score
    std = stats["std_amount"] if stats["std_amount"] > 0 else 1
    amount_zscore = abs((transaction["amount"] - stats["avg_amount"]) / std)

    # 2️⃣ Country change
    country_change_flag = int(
        transaction["country"] != stats["most_common_country"]
    )

    # 3️⃣ Device change
    device_change_flag = int(
        transaction["device_id"] != stats["most_common_device"]
    )

    # 4️⃣ Burst detection (5+ tx within 10 minutes)
    recent_tx = user_history[
        (user_history["timestamp"] >= transaction["timestamp"] - pd.Timedelta(minutes=10)) &
        (user_history["timestamp"] <= transaction["timestamp"])
    ]

    burst_flag = int(len(recent_tx) >= 5)

    # Normalize z-score
    normalized_z = min(amount_zscore / 5, 1)

    # Weighted risk score
    # Country change and burst are high-severity indicators
    risk_score = (
        0.15 * normalized_z +
        0.50 * country_change_flag +
        0.10 * device_change_flag +
        0.25 * burst_flag
    )

    risk_score = round(float(risk_score), 3)

    return {
        "transaction": {
            "transaction_id": transaction["transaction_id"],
            "amount": float(transaction["amount"]),
            "country": transaction["country"],
            "device_id": transaction["device_id"],
            "timestamp": str(transaction["timestamp"])
        },
        "behavioral_metrics": {
            "amount_zscore": round(float(amount_zscore), 3),
            "country_change_flag": country_change_flag,
            "device_change_flag": device_change_flag,
            "burst_flag": burst_flag
        },
        "risk_score": risk_score
    }

if __name__ == "__main__":
    from data_generator import generate_synthetic_data

    df = generate_synthetic_data()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    user_stats = compute_user_baseline(df)

    sample_tx = df.iloc[5000]
    user_history = df[df["user_id"] == sample_tx["user_id"]]

    result = compute_risk(sample_tx, user_stats, user_history)

    print(result)