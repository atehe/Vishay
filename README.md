## **Vishay Website Scraper**

This project contains a python script using scrapy to crawl the navigation menu and data from vishay.com.
It is designed to extract the hierarchical topic structure, including categories, sub-categories, and product links, and save the results to a JSON file.

### **Why Scrapy?**

The technical requirements for this project specified a recursive scraper.
While it is possible to build such a scraper manually using libraries like requests and beautifulsoup, scrapy is the ideal choice for this type of task because it is inherently designed for recursive crawling.

- **Built-in Recursion**: Scrapy's core architecture handles asynchronous requests and callback management automatically. Instead of writing complex, explicit recursive loops, you simply yield a new Request object. Scrapy takes care of fetching the new URL and feeding its response back to the specified parsing function, which greatly simplifies the code.
- **Robustness and Efficiency**: Scrapy is an event-driven framework that can handle thousands of concurrent requests without significant resource overhead, making it highly efficient for large-scale crawling. It also includes built-in features for handling redirects, retries, and rate limiting.
- **Extensibility**: Scrapy provides a clean, component-based structure (spiders, pipelines, middlewares) that makes it easy to add features like custom data processing, logging, and error handling.

### **Prerequisites**

- Python 3.x

### **Installation**

First, clone this code. Then, install the required libraries using `pip` and the provided `requirements.txt` file.

```
pip install -r requirements.txt
```

### **Usage**

To run the scraper, execute the script from your command line.
The `--out` argument is optional; if omitted, the output will be saved to `topic_structure.json` by default.

```
python3 vishay_scraper.py --out my_output_file.json
```

### **Project Notes and Design Decisions**

This script was developed as a test project, and as a result, a few deliberate design choices were made to demonstrate core scraping concepts.

**Breadcrumbs:** When navigating the Vishay website, two types of breadcrumbs are available: the one we build recursively as we follow tags/links, and the one that is displayed on the top left of some pages like the catagory and product page.

This script uses the recursively-generated breadcrumb but uses the one on the page when it is available. This approach can be refactored based on your needs.

**Targeted Parsing:** The navigation structure on vishay.com varies between different navigation menus (e.g., "Products," "Applications," "Resources"). For this test project, the scraper was written to only parse the menu structure found under the `"Products"` tab.

In a full-scale project, we can extend the spider's logic to handle each unique layout. This would involve writing specific parsing functions for each section and directing the crawler to the correct function based on the URL or content.

**Product Node:** The product table on the site has a dynamic structure, making it difficult to parse into the required format. For this reason, we extract headers of the product table and use them as attributes to the product node. We also combine them with the standard node attributes like `url`, `sub_topics`, `breadcrumbs`.

This ensures that the output remains valid even if the product table columns changes

## **Potential Improvements**

The current script setup stores the entire scraped data structure in memory (`self.results`) before writing it to a file. For very large websites, this can lead to high memory usage. A more scalable approach would be to use a [Scrapy Item Pipeline](https://docs.scrapy.org/en/latest/topics/item-pipeline.html).

Instead of appending to an in-memory list, the spider would yield each final item (e.g., each product or category) as it is discovered. The item pipeline would then be configured to process and write each item to a file, database, or other storage system incrementally, eliminating the need to hold the entire dataset in RAM.
