import pandas as pd

# 读取 CSV 文件
df = pd.read_csv("core/parsed_cowrie_test_commands.csv")

# 删除 input 列中值为 'unknown' 的行
df_cleaned = df[df["input"] != "unknown"]

# 保存到新文件
df_cleaned.to_csv("core/parsed_cowrie_test_commands.csv", index=False)

print(f"清理完成！原始行数：{len(df)}，清理后行数：{len(df_cleaned)}")
