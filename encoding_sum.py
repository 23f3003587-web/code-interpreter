import pandas as pd

# The three symbols we care about (use the real Unicode characters)
symbols = ['œ', '‘', '•']

# --- data1.csv: CP-1252 ---
df1 = pd.read_csv('data1.csv', encoding='cp1252')   # or 'windows-1252'
print("data1.csv preview:")
print(df1.head())
sum1 = df1[df1['symbol'].isin(symbols)]['value'].sum()
print(f"Sum for matching symbols in data1: {sum1}\n")

# --- data2.csv: UTF-8 ---
df2 = pd.read_csv('data2.csv', encoding='utf-8')
print("data2.csv preview:")
print(df2.head())
sum2 = df2[df2['symbol'].isin(symbols)]['value'].sum()
print(f"Sum for matching symbols in data2: {sum2}\n")

# --- data3.txt: UTF-16 (tab-separated) ---
# utf-16 automatically handles BOM if present
df3 = pd.read_csv('data3.txt', encoding='utf-16', sep='\t')
print("data3.txt preview:")
print(df3.head())
sum3 = df3[df3['symbol'].isin(symbols)]['value'].sum()
print(f"Sum for matching symbols in data3: {sum3}\n")

# Total
total = sum1 + sum2 + sum3
print(f"=== TOTAL SUM across all three files for œ OR ‘ OR • : {total} ===")