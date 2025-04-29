🕵️‍♂️ Amazon Scraping Utility
Welcome to one scraper shop for Amazon motherboard data!
This tool helps you track prices, rankings, and seller info — whether you're chasing Best Sellers or analyzing a custom ASIN list.

Built with Selenium, BeautifulSoup, and a pinch of anti-captcha.

🧠 What This Tool Does

✅ scrape_best_sellers()
Scrapes the top-N best-selling motherboards on Amazon and pulls detailed product info:

ASIN

Product title, price, seller type

Ratings, Best Sellers Rank, and more

Perfect for building your own competitive intel dashboard.

✅ runrate_scraper()
Reads a spreadsheet of ASINs (from base_asins_RunRate.xlsx)
Fetches product metadata and compiles it into an Excel file.

Use this if you already have a product list and just want to refresh key details.

💻 How to Use It

You'll need:

selenium

webdriver-manager

beautifulsoup4

pandas

openpyxl (for Excel I/O)

▶️ Run the Scraper

Option 1: Scrape Best Sellers

python amazon_scraper.py
# or call scrape_best_sellers() inside the script

Option 2: Scrape from ASIN list

Uncomment the following in the script:

# runrate_scraper()
Or call programmatically:

from amazon_scraper import runrate_scraper
runrate_scraper("your_asin_file.xlsx")

🧠 Features

Randomized user agents to avoid basic bot detection

Headless Chrome support

Captcha detection + skip logic

Simple Excel/CSV output

Modular structure (shared parser, easy to maintain)

📌 Example Output

![image](https://github.com/user-attachments/assets/2bdcd2b5-542e-4e8a-8451-1f68a8b47899)
