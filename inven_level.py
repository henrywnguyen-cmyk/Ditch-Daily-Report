import requests
import pandas as pd
import datetime
import os

# Shopify API credentials 
SHOP_URL = "..."
ACCESS_TOKEN = "..."
API_VERSION = "..."

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}

# get all products with variants
def get_all_products():
    all_products = []
    url = f"{SHOP_URL}/admin/api/{API_VERSION}/products.json"
    
    while url:
        print(f"📡 Fetching products...")
        response = requests.get(url, headers=HEADERS, params={"limit": 250})
        
        if response.status_code != 200:
            print(f" Error {response.status_code}: {response.text}")
            break
            
        data = response.json()
        products = data.get("products", [])
        all_products.extend(products)
        
        # check for next page
        link_header = response.headers.get('Link', '')
        if 'rel="next"' in link_header:
            # Extract next URL from Link header
            next_url = None
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    next_url = link.split(';')[0].strip('<> ')
                    break
            url = next_url
        else:
            url = None
    
    print(f" Found {len(all_products)} products")
    return all_products

# extract inventory items
def extract_inventory_items(products):
    inventory_items = []
    
    for product in products:
        for variant in product.get("variants", []):
            inventory_items.append({
                "product_title": product["title"],
                "variant_title": variant.get("title", "Default Title"),
                "sku": variant.get("sku", ""),
                "inventory_item_id": variant["inventory_item_id"],
                "variant_id": variant["id"]
            })
    
    print(f" Extracted {len(inventory_items)} inventory items")
    return inventory_items

# get inventory levels 
def get_inventory_levels(inventory_items):
    item_ids = [item["inventory_item_id"] for item in inventory_items]
    all_levels = []
    batch_size = 50
    
    for i in range(0, len(item_ids), batch_size):
        batch = item_ids[i:i+batch_size]
        print(f"Fetching inventory levels batch {i//batch_size + 1}...")
        
        url = f"{SHOP_URL}/admin/api/{API_VERSION}/inventory_levels.json"
        params = {
            "inventory_item_ids": ",".join(str(iid) for iid in batch)
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            continue
            
        levels = response.json().get("inventory_levels", [])
        all_levels.extend(levels)
    
    print(f"Found {len(all_levels)} inventory levels")
    return all_levels

# match items with levels
def match_inventory_data(inventory_items, inventory_levels):
    # Create lookup dictionary for faster matching
    levels_dict = {level["inventory_item_id"]: level for level in inventory_levels}
    
    matched_data = []
    
    for item in inventory_items:
        inventory_item_id = item["inventory_item_id"]
        level = levels_dict.get(inventory_item_id, {})
        
        matched_data.append({
            "product_title": item["product_title"],
            "variant_title": item["variant_title"],
            "sku": item["sku"],
            "inventory_item_id": inventory_item_id,
            "available": level.get("available", 0),
            "location_id": level.get("location_id", ""),
        })
    
    print(f"Matched {len(matched_data)} items with inventory levels")
    return matched_data

# save report
def save_inventory_report(inventory_data, filename):
    df = pd.DataFrame(inventory_data)
    
    # Sort by available stock from highest to lowest
    df = df.sort_values('available', ascending=False)
    
    df.to_csv(filename, index=False)
    print(f"Report saved: {filename}")
    print(f"Total items: {len(df)}")
    print(f"Items with stock: {len(df[df['available'] > 0])}")
    print(f"Out of stock: {len(df[df['available'] == 0])}")
    print(f"Sorted by stock level: Highest to Lowest")

    # shows top 10 items with highest stock
    print(f"\n🔝 Top 10 items with highest stock:")
    top_10 = df.head(10)
    for idx, row in top_10.iterrows():
        print(f"   {row['product_title'][:40]:<40} | {row['variant_title']:<10} | Stock: {row['available']:>3}")
    
    return df

# main execution 
if __name__ == "__main__":
    print("🚀 Starting Shopify inventory sync...")
    
    # generate today's filename
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    inventory_filename = f"inventory_report_{today_str}.csv"
    
    try:
        products = get_all_products()
        
        inventory_items = extract_inventory_items(products)
        
        inventory_levels = get_inventory_levels(inventory_items)

        matched_inventory = match_inventory_data(inventory_items, inventory_levels)

        save_inventory_report(matched_inventory, inventory_filename)
        
        print(f"Inventory sync complete!")
        print(f"Report saved as: {inventory_filename}")
        print(f"Data sorted: Highest stock → Lowest stock")
        
    except Exception as e:
        print(f"Error during sync: {e}")
