import scrapy
from scrapy.crawler import CrawlerProcess

import re
import argparse
import json
from pathlib import Path


def clean(string, sep=" "):
    if isinstance(string, list):
        string = sep.join([s for s in string if s])
    if not string:
        return None
    string = str(string)
    string = string.replace("\r", " ").replace("\\r", " ")
    string = string.replace("\n", " ").replace("\\n", " ")
    string = string.replace("\t", " ").replace("\\t", " ")
    string = re.sub(r"\s+", " ", string)
    return string.strip()


class VishaySpider(scrapy.Spider):
    name = "vishay"

    def __init__(self, out="topic_structure.json", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = ["https://www.vishay.com/"]
        self.results = []
        self.out_file = out

    def closed(self, reason):
        """Write results to JSON after spider closes"""
        Path(self.out_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.out_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=4, ensure_ascii=False)

    def parse(self, response):
        menus = response.xpath('//ul[@id="ulMenuLinks"]/li')

        for menu in menus:
            menu_name = clean(menu.xpath("./a//text()").get())
            self.logger.info(f"Processing menu: {menu_name}...")

            if "product" not in menu_name.lower():
                continue
                # TODO: add support for other menu structure

            node = {
                "name": menu_name,
                "url": None,
                "sub_topics": [],
                "breadcrumbs": [menu_name],
            }

            groups = menu.xpath('.//div[@class="vsh-column-title"]')
            for group in groups:
                group_name = clean(group.xpath("./div/span/text()").get())
                group_node = {
                    "name": group_name,
                    "url": None,
                    "sub_topics": [],
                    "breadcrumbs": node["breadcrumbs"] + [group_name],
                }

                menu_items = group.xpath('.//div[@class="vsh-mm-accordion"]')
                for sub_menu in menu_items:
                    sub_name = clean(" ".join(sub_menu.xpath(".//text()").getall()))
                    sub_node = {
                        "name": sub_name,
                        "url": None,
                        "sub_topics": [],
                        "breadcrumbs": group_node["breadcrumbs"] + [sub_name],
                    }

                    submenu_items = sub_menu.xpath(
                        './following-sibling::div[@class="vsh-mm-home-content"][1]//a'
                    )
                    for i, inner in enumerate(submenu_items):
                        item_name = clean(inner.xpath(".//text()").get())
                        item_url = response.urljoin(inner.xpath(".//@href").get())
                        item_node = {
                            "name": item_name,
                            "url": item_url,
                            "sub_topics": [],
                            "breadcrumbs": sub_node["breadcrumbs"] + [item_name],
                        }
                        sub_node["sub_topics"].append(item_node)

                        # Schedule request to expand categories/products
                        if item_url:
                            yield scrapy.Request(
                                item_url,
                                callback=self.parse_category,
                                meta={"node": item_node},
                            )

                    group_node["sub_topics"].append(sub_node)

                node["sub_topics"].append(group_node)

            self.results.append(node)

    def parse_category(self, response):
        """Parse category pages: expand into subcategories or products"""
        parent_node = response.meta["node"]
        bread_crumbs = response.xpath(
            '//div[contains(@class, "Breadcrumb")]//span[@key]/@key|//div[contains(@class, "Breadcrumb")]//a/text()'
        ).getall()

        # Products table
        if response.xpath('//table[@id="poc"]'):
            self.logger.info(f"Found products at {response.url}")
            # get headers dynamically
            headers = response.xpath('//table[@id="poc"]//th')
            headers = [clean(h.xpath(".//text()").get()) for h in headers]

            for tr in response.xpath('//table[@id="poc"]//tbody//tr'):
                values = tr.xpath(".//td")
                values = [clean(v.xpath(".//text()").getall()) for v in values]
                product_node = dict(zip(headers, values))
                product_node["url"] = (
                    response.urljoin(
                        tr.xpath(".//a[contains(@href, 'product')]/@href").get()
                    )
                    if tr.xpath(".//a[contains(@href, 'product')]/@href").get()
                    else None
                )
                product_node["sub_topics"] = []
                product_node["breadcrumbs"] = bread_crumbs

                parent_node["sub_topics"].append(product_node)

        # Case 2: Subcategories
        else:
            self.logger.info(f"Found categories at {response.url}")
            categories = response.xpath(".//dl")
            for category in categories:
                cat_name = clean(category.xpath(".//dt//text()").get())

                cat_node = {
                    "name": cat_name,
                    "url": None,
                    "sub_topics": [],
                    "breadcrumbs": bread_crumbs + [cat_name],
                }
                subcategories = category.xpath(".//dd//li")

                for subcategory in subcategories:
                    sub_name = clean(subcategory.xpath(".//text()").get())
                    sub_url = response.urljoin(subcategory.xpath(".//@href").get())

                    sub_node = {
                        "name": sub_name,
                        "url": sub_url,
                        "sub_topics": [],
                        "breadcrumbs": cat_node["breadcrumbs"] + [sub_name],
                    }
                    cat_node["sub_topics"].append(sub_node)

                    if sub_url:
                        yield scrapy.Request(
                            sub_url,
                            callback=self.parse_category,
                            meta={"node": sub_node},
                        )
                parent_node["sub_topics"].append(cat_node)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Vishay menu structure")
    parser.add_argument(
        "--out", default="topic_structure.json", help="Output JSON file"
    )
    args = parser.parse_args()

    process = CrawlerProcess(
        settings={
            "LOG_LEVEL": "INFO",
        }
    )
    process.crawl(VishaySpider, out=args.out)
    process.start()
