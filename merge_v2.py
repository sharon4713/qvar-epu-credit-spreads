import pandas as pd
import os

base = r'C:\Users\simeo\OneDrive\Desktop\qvar'

df_main = pd.read_csv(os.path.join(base, 'US_merged.csv'), parse_dates=['date'])
df_main = df_main.rename(columns={'News_Based_Policy_Uncert_Index': 'EPU'})

df_baa = pd.read_excel(os.path.join(base, 'USBAA.xlsx'),sheet_name="Monthly")
df_baa['date'] = pd.to_datetime(df_baa['observation_date'])
baa_col = [c for c in df_baa.columns if c not in ('observation_date', 'date')][0]
df_baa = df_baa[['date', baa_col]].rename(columns={baa_col: 'DBAA'})
df_baa['DBAA'] = pd.to_numeric(df_baa['DBAA'], errors='coerce')
df_baa = df_baa.dropna(subset=['DBAA'])

df_aaa = pd.read_excel(os.path.join(base, 'USAAA.xlsx'),sheet_name="Monthly")
df_aaa['date'] = pd.to_datetime(df_aaa['observation_date'])
aaa_col = [c for c in df_aaa.columns if c not in ('observation_date', 'date')][0]
df_aaa = df_aaa[['date', aaa_col]].rename(columns={aaa_col: 'DAAA'})
df_aaa['DAAA'] = pd.to_numeric(df_aaa['DAAA'], errors='coerce')
df_aaa = df_aaa.dropna(subset=['DAAA'])

df = df_main.merge(df_baa, on='date', how='inner').merge(df_aaa, on='date', how='inner')
df['bbb_aaa_spread'] = df['DBAA'] - df['DAAA']
df = df[['date', 'EPU', 'credit_spread', 'yield_curve_slope', 'bbb_aaa_spread']]

out = os.path.join(base, 'US_merged_v2.csv')
df.to_csv(out, index=False)

print(f"Saved: {out}")
print(f"Shape: {df.shape}")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(df.head())
