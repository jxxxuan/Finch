from database import create_conn
import pandas as pd
# make sure convert nan index to "NA" 
# df.to_csv('G:\My Drive\stock\symbol.tsv', sep='\t', na_rep='\\N')
# index must have pandas name

conn = create_conn()
df = pd.read_csv(r'G:\My Drive\stock\symbol.tsv',sep='\t',na_values='\\N',index_col=0)
cols = df.columns

cur = conn.cursor()

# Drop symbol table if exists
cur.execute("DROP TABLE IF EXISTS symbol;")
conn.commit()

# Create symbol table
sql = "CREATE TABLE symbol (\n    symbol text PRIMARY KEY,\n"

for c in cols:
    if 'record' in c or c == 'delisted':
        sql += f"    {c} boolean,\n"
    elif 'update' in c or 'first_day' in c or 'last_day' in c:
        if 'first_day' in c or 'last_day' in c:
            sql += f"    {c} timestamptz,\n"
        else:
            sql += f"    {c} timestamp,\n"
    else:
        sql += f"    {c} text,\n"

sql = sql.rstrip(',\n') + "\n);"
cur.execute(sql)
conn.commit()

# Insert data into symbol table from csv
with open(r'G:\My Drive\stock\symbol.tsv', 'r', encoding='utf-8') as f:
    next(f)  # skip header
    cur.copy_from(f, 'symbol', sep='\t', null='\\N')

conn.commit()

cur.close()
conn.close()
print('done')