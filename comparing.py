import pandas as pd

# load yesterday's inventory
yesterday_df = pd.read_csv("old_cleaned.csv")

# load today's inventory
today_df = pd.read_csv("inventory_report_2025-08-29.csv")

# create matching keys using product title + variant title
yesterday_df['product_key'] = yesterday_df['Product Title'] + ' - ' + yesterday_df['Variant Title'].fillna('Default Title')
today_df['product_key'] = today_df['product_title'] + ' - ' + today_df['variant_title'].fillna('Default Title')

# Merge on product_key (name-based matching)
merged = pd.merge(
    yesterday_df,
    today_df,
    on="product_key",
    suffixes=("_yesterday", "_today")
)

# calculate decrease
merged["decrease"] = merged["Inventory Available"] - merged["available"]

# only show items that decreased
decreased_items = merged[merged["decrease"] > 0]

# sort by most decreased
decreased_items = decreased_items.sort_values(by="decrease", ascending=False)

# debug: Print available columns to see what we have
print("Available columns after merge:")
print(decreased_items.columns.tolist())

# select relevant columns for the report (using correct column names after merge)
report_columns = [
    'Product Title',
    'Variant Title', 
    'SKU',  # This should be the original SKU column from yesterday
    'Inventory Available',
    'available',
    'decrease'
]

final_report = decreased_items[report_columns].copy()
final_report.columns = [
    'Product Title',
    'Variant Title',
    'SKU',
    'Yesterday Stock',
    'Today Stock', 
    'Decrease Amount'
]

# save to new CSV
final_report.to_csv("inventory_decrease_report.csv", index=False)

print(f"✅ Saved inventory_decrease_report.csv")
print(f"📉 Found {len(final_report)} items with decreased inventory")
print(f"📊 Total decrease: {final_report['Decrease Amount'].sum()} units")

# show top 10 biggest decreases
print(f"\n🔝 Top 10 biggest decreases:")
for idx, row in final_report.head(10).iterrows():
    print(f"   {row['Product Title'][:40]:<40} | {row['Variant Title']:<10} | -{row['Decrease Amount']:>3.0f}")