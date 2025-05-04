import pandas as pd

def analyze_feedback(csv_path="feedback_log.csv"):
    if not os.path.exists(csv_path):
        print("Belum ada feedback.")
        return

    df = pd.read_csv(csv_path)

    # Ambil skor dari isi sinyal
    def extract_score(text):
        match = re.search(r"Score: (\d+)/6", text)
        return int(match.group(1)) if match else None

    df["score"] = df["signal"].apply(extract_score)

    # Ringkasan jumlah feedback per skor
    summary = df.groupby(["score", "feedback"]).size().unstack(fill_value=0)

    print("Ringkasan feedback berdasarkan skor:")
    print(summary)

    # Contoh logika evaluasi awal:
    for score in range(7):
        total = summary.loc[score].sum() if score in summary.index else 0
        if total == 0: continue
        up_ratio = summary.loc[score]["up"] / total if "up" in summary.columns else 0
        down_ratio = summary.loc[score]["down"] / total if "down" in summary.columns else 0
        if up_ratio < 0.3 and down_ratio > 0.5:
            print(f"⚠️ Skor {score} terlalu tinggi, banyak rugpull.")
        elif up_ratio > 0.7:
            print(f"✅ Skor {score} cukup akurat untuk sinyal bagus.")
