# --- 簡易パスワード機能 ---
password = st.text_input("パスワードを入力してください", type="password")
if password != "msgplus":
    st.warning("パスワードが違います")
    st.stop()  # ここで処理を止める
    
import streamlit as st
import pandas as pd
import io

# -----------------------------
# 公式リスト
# -----------------------------
OFFICIAL_LIST = [
    "VERBAL","RAMPAGE","ELLY","塩野瑛久","鈴木伸之","町田啓太","小野塚勇人",
    "クリスタルケイ","石井杏奈","佐田真由美","佐藤晴美","早乙女太一","D.I",
    "黒井さん","ami","藤井夏恋","DEEP","WHH","TJBB","LIL LEAGUE","KID",
    "RIKACO","girls2","lucky2","MIYAVI","RAGPOUND","山口乃々華","真砂さん",
    "A&Rルーム","TAKU"
]

# -----------------------------
# CSV読み込み（文字コード自動判定）
# -----------------------------
def read_csv_safe(file):

    encodings = ["cp932","shift_jis","utf-8-sig","utf-8"]

    for enc in encodings:
        try:
            file.seek(0)
            return pd.read_csv(file,encoding=enc)
        except:
            continue

    st.error("CSVの文字コードを判定できませんでした")
    st.stop()


# -----------------------------
# 時間変換
# -----------------------------
def to_min(s):

    try:
        s=str(s)

        if ":" in s:
            h,m=s.split(":")[:2]
            return int(h)*60+int(m)

        return float(s)

    except:
        return 0


def to_str(m):

    h=int(m//60)
    m=int(m%60)

    return f"{h:02d}:{m:02d}:00"


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🚗 車両運行集計アプリ")

st.write("kintoneから出力したCSVをアップロードしてください")

uploaded_file = st.file_uploader("CSVファイルを選択", type="csv")


# -----------------------------
# メイン処理
# -----------------------------
if uploaded_file is not None:

    df = read_csv_safe(uploaded_file)

    # 列名の空白削除
    df.columns = df.columns.str.strip()

    try:

        # フィルタ
        df_f = df[df['送迎グループ/役員名'].isin(OFFICIAL_LIST)].copy()

        # 分に変換
        df_f['mins'] = df_f['合計(使用時間合計)'].apply(to_min)

        # -------------------------
        # シート1 集計
        # -------------------------
        summary = df_f.groupby(
            ['送迎グループ/役員名','車両番号']
        )['mins'].sum().reset_index()

        person_total = df_f.groupby(
            '送迎グループ/役員名'
        )['mins'].sum().reset_index()

        summary['稼働時間合計'] = summary['mins'].apply(to_str)

        summary['担当ごとの合計'] = ""

        # 担当ごと合計
        for person in person_total['送迎グループ/役員名']:

            idx = summary[summary['送迎グループ/役員名']==person].index

            total_val = person_total[
                person_total['送迎グループ/役員名']==person
            ]['mins'].values[0]

            summary.loc[idx[0],'担当ごとの合計']=to_str(total_val)

        # 総合計
        grand_total = df_f['mins'].sum()

        summary.loc[len(summary)] = {
            '送迎グループ/役員名':'総合計',
            '車両番号':'',
            'mins':'',
            '稼働時間合計':'',
            '担当ごとの合計':to_str(grand_total)
        }

        # -------------------------
        # シート2 詳細
        # -------------------------
        detail = df_f[
            ['運転年月日 (日単位)','合計(使用時間合計)','送迎グループ/役員名','車両番号']
        ].copy()

        detail.columns = ['日付','稼働時間','利用者','車両']

        # -------------------------
        # Excel作成
        # -------------------------
        output = io.BytesIO()

        with pd.ExcelWriter(output,engine="openpyxl") as writer:

            summary[
                ['送迎グループ/役員名','車両番号','稼働時間合計','担当ごとの合計']
            ].to_excel(writer,sheet_name="稼働時間合計",index=False)

            detail.to_excel(writer,sheet_name="稼働日詳細",index=False)

        st.success("集計完了")

        st.download_button(
            label="Excelダウンロード",
            data=output.getvalue(),
            file_name="運行集計結果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error("処理中にエラーが発生しました")

        st.write(e)
