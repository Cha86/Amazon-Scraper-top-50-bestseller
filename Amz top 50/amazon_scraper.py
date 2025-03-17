import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# -------------------------------------------------------------------------
# 1) Initialize WebDriver
# -------------------------------------------------------------------------
def init_driver(headless=True):
    """
    Initialize and return the Chrome WebDriver with optional headless mode.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Mimic a regular browser user agent to reduce blocking
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
    
    # Optional: Disable extensions and automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Initialize the WebDriver
    service = Service()  # Assumes chromedriver is in PATH
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional step to prevent detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# -------------------------------------------------------------------------
# 2) Scrape the top 50 products from the Best Sellers page
# -------------------------------------------------------------------------
def get_top_50_products(driver, best_sellers_url):
    """
    Navigate to the Best Sellers page and extract the top 50 products with their rank and URLs.
    Returns a list of dictionaries with 'rank', 'product_url', and 'ASIN'.
    """
    driver.get(best_sellers_url)
    
    # Wait until the product grid is loaded by waiting for the presence of product items
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.zg-item-immersion"))
        )
    except Exception as e:
        print(f"Error loading Best Sellers page: {e}")
        # Optional: Save the page source for debugging
        with open("error_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return []
    
    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Locate the ordered list containing the products
    product_list = soup.find('ol', class_='zg-ordered-list')
    if not product_list:
        print("Could not find the product list on the page.")
        return []
    
    # Each product is within an <li> tag inside the <ol class="zg-ordered-list">
    product_items = product_list.find_all('li', class_='zg-item-immersion', limit=50)
    if not product_items:
        print("No products found. Check the page structure and selectors.")
        return []
    
    products_list = []
    for idx, product in enumerate(product_items, start=1):
        # 1) Rank: Typically in <span class="zg-badge-text">#1</span>
        rank_tag = product.find('span', class_='zg-badge-text')
        rank = rank_tag.get_text(strip=True) if rank_tag else "N/A"
        
        # 2) Product URL: Inside the <a> tag with class 'a-link-normal'
        link_tag = product.find('a', class_='a-link-normal')
        if link_tag and link_tag.get('href'):
            product_url = "https://www.amazon.com" + link_tag['href'].split('?')[0]  # Remove query params
        else:
            product_url = "N/A"
        
        # Optional: Extract ASIN from the product URL
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
        asin = asin_match.group(1) if asin_match else "N/A"
        
        products_list.append({
            'rank': rank,
            'product_url': product_url,
            'ASIN': asin
        })
    
    print(f"Found {len(products_list)} products.")
    return products_list

# -------------------------------------------------------------------------
# 3) Scrape details from each product's detail page
# -------------------------------------------------------------------------
def get_product_details(driver, product_url):
    """
    Given a product URL, scrape details such as vendor, model, chipset, price, rating, seller type, condition type, and best sellers rank.
    Returns a dictionary with the extracted data.
    """
    if product_url == "N/A":
        return {
            "Product Name": "N/A",
            "Vendor": "N/A",
            "Model": "N/A",
            "Chipset": "N/A",
            "Rating": "N/A",
            "Best Sellers Rank": "N/A",
            "Product Price": "N/A",
            "Seller Type": "N/A",
            "Condition Type": "N/A",
            "Product URL": product_url,
        }
    
    driver.get(product_url)
    
    # Wait until the product title is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )
    except Exception as e:
        print(f"Error loading product page {product_url}: {e}")
        # Optional: Save the page source for debugging
        with open("error_product_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return {
            "Product Name": "N/A",
            "Vendor": "N/A",
            "Model": "N/A",
            "Chipset": "N/A",
            "Rating": "N/A",
            "Best Sellers Rank": "N/A",
            "Product Price": "N/A",
            "Seller Type": "N/A",
            "Condition Type": "N/A",
            "Product URL": product_url,
        }
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # ------------------------------------------------
    # 1) Product Name
    # ------------------------------------------------
    try:
        product_name = soup.find(id="productTitle").get_text(strip=True)
    except AttributeError:
        product_name = "N/A"
    
    # ------------------------------------------------
    # 2) Product Price
    # ------------------------------------------------
    product_price = "N/A"
    price_selectors = [
        '#corePriceDisplay_desktop_feature_div span.a-offscreen',
        '#corePriceDisplay_mobile_feature_div span.a-offscreen',
        'span#price_inside_buybox',
        'span.a-price.a-text-price.a-size-medium .a-offscreen'
    ]
    for sel in price_selectors:
        price_tag = soup.select_one(sel)
        if price_tag:
            raw = price_tag.get_text(strip=True).replace('$', '').replace(',', '')
            if re.match(r'^\d+(\.\d+)?$', raw):
                product_price = float(raw)
                break
    if product_price == "N/A":
        # Fallback: Find all price spans and exclude unwanted ones
        for pt in soup.find_all('span', class_='a-offscreen'):
            parent_text = pt.find_parent().get_text(" ", strip=True).lower()
            if any(kw in parent_text for kw in ["protection plan", "warranty", "asurion"]):
                continue  # Skip unwanted price elements
            raw = pt.get_text(strip=True).replace('$', '').replace(',', '')
            if re.match(r'^\d+(\.\d+)?$', raw):
                try:
                    product_price = float(raw)
                    break
                except ValueError:
                    continue
    
    # ------------------------------------------------
    # 3) Seller Info (Amazon vs 3rd Party)
    # ------------------------------------------------
    try:
        ships_from = soup.find(string=re.compile("Ships from", re.I))
        sold_by = soup.find(string=re.compile("Sold by", re.I))
        ships_from_info = ships_from.find_next().get_text(strip=True) if ships_from else ""
        sold_by_info = sold_by.find_next().get_text(strip=True) if sold_by else ""
        seller_type = "Amazon" if "Amazon.com" in ships_from_info or "Amazon.com" in sold_by_info else "3rd Party"
    except AttributeError:
        seller_type = "N/A"
    
    # ------------------------------------------------
    # 4) Condition Type (New / Used / etc.)
    # ------------------------------------------------
    try:
        buy_new_button = soup.find('input', {'id': 'add-to-cart-button'})
        buy_used_section = soup.find('div', {'id': 'olpLinkWidget_feature_div'})
        if buy_new_button:
            condition_type = "New"
        elif buy_used_section:
            condition_type = "Used"
        else:
            condition_type = "N/A"
    except Exception:
        condition_type = "N/A"
    
    # ------------------------------------------------
    # 5) Vendor, Model, Chipset, Rating
    # ------------------------------------------------
    # Vendor
    vendor = "N/A"
    vendor_tag = soup.select_one('span.a-size-base.po-break-word')
    if not vendor_tag:
        # Alternate selector
        vendor_tag = soup.select_one('a.contributorNameID')
    if vendor_tag:
        vendor = vendor_tag.get_text(strip=True)
    
    # Model
    model = "N/A"
    model_label = soup.find('td', string=re.compile("Model", re.I))
    if model_label:
        model_td = model_label.find_next('td')
        if model_td:
            model = model_td.get_text(strip=True)
    
    # Chipset
    chipset = "N/A"
    chipset_label = soup.find('td', string=re.compile("Chipset", re.I))
    if chipset_label:
        chipset_td = chipset_label.find_next('td')
        if chipset_td:
            chipset = chipset_td.get_text(strip=True)
    
    # Rating
    rating = "N/A"
    rating_tag = soup.select_one('span.a-icon-alt')
    if rating_tag:
        rating_text = rating_tag.get_text(strip=True)
        match = re.match(r'^(\d+(\.\d+)?) out of 5 stars', rating_text)
        if match:
            rating = float(match.group(1))
    
    # ------------------------------------------------
    # 6) Best Sellers Rank
    # ------------------------------------------------
    best_sellers_rank = "N/A"
    # First attempt: Check for id='SalesRank'
    bsr_section = soup.find(id='SalesRank')
    if bsr_section:
        bsr_text = bsr_section.get_text(" ", strip=True)
        match = re.search(r'#(\d+)', bsr_text)
        if match:
            best_sellers_rank = f"#{match.group(1)}"
    else:
        # Fallback: Check within 'Product details'
        bsr_section = soup.find('span', string=re.compile("Best Sellers Rank", re.I))
        if bsr_section:
            bsr_text = bsr_section.get_text(" ", strip=True)
            match = re.search(r'#(\d+)', bsr_text)
            if match:
                best_sellers_rank = f"#{match.group(1)}"
    
    return {
        "Product Name": product_name,
        "Vendor": vendor,
        "Model": model,
        "Chipset": chipset,
        "Rating": rating,
        "Best Sellers Rank": best_sellers_rank,
        "Product Price": product_price,
        "Seller Type": seller_type,
        "Condition Type": condition_type,
        "Product URL": product_url,
    }

# -------------------------------------------------------------------------
# 4) Main function to coordinate scraping
# -------------------------------------------------------------------------
def main():
    # Initialize WebDriver
    driver = init_driver(headless=False)  # Set headless=True for no browser UI
    
    # Best Sellers URL for Computer Motherboards
    best_sellers_url = (
        "https://www.amazon.com/Best-Sellers-Computers-Accessories-Computer-Motherboards/"
        "zgbs/pc/1048424/ref=zg_bs_pg_1_pc?_encoding=UTF8&pg=1"
    )
    
    # Step 1: Get Top 50 Products
    top_products = get_top_50_products(driver, best_sellers_url)
    if not top_products:
        print("No products found. Exiting.")
        driver.quit()
        return
    
    # Step 2: Scrape Details for Each Product
    scraped_data = []
    for prod in top_products:
        rank = prod['rank']
        product_url = prod['product_url']
        asin = prod['ASIN']
        
        print(f"Scraping details for Rank {rank} | ASIN: {asin} | URL: {product_url}")
        details = get_product_details(driver, product_url)
        if details:
            details["Rank"] = rank
            scraped_data.append(details)
    
    # Close the WebDriver
    driver.quit()
    
    # Step 3: Save to CSV
    field_names = [
        "Rank",
        "Product Name",
        "Vendor",
        "Model",
        "Chipset",
        "Rating",
        "Best Sellers Rank",
        "Product Price",
        "Seller Type",
        "Condition Type",
        "Product URL",
    ]
    
    with open('amazon_top_50_products.csv', 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        for data in scraped_data:
            writer.writerow(data)
    
    print("Scraping completed. Data saved to 'amazon_top_50_products.csv'.")

# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
