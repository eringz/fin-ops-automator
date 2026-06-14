import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CrawlResult, DefaultMarkdownGenerator,  PruningContentFilter, CacheMode, LLMConfig, LLMExtractionStrategy
from typing import List
import json
from pathlib import Path
import base64

__cur_dir__ = Path(__file__).resolve().parent

async def demo_basic_crawl():
    print("\n=== 1. Basic Web Crawling ===")
    
    # async with AsyncWebCrawler as crawler:
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            url="https://clickpay.cpi-outsourcing.com/"
        )
        
        for i, result in enumerate(results):
            print(f"Result: { i + 1}:")
            print(f"Success: {result.success}")
            
            if result.success:
                print(f"Markdown length: {len(result.markdown.raw_markdown)} chars")
                print(f"First 100 chars: {result.markdown.raw_markdown[:100]}...")
                # print(f"First 100 chars: {result.cleaned_html}...")
            else:
                print("Failed to crawl the URL")
                
async def demo_parallel_crawl():
    print("\n=== 2. Parallel Crawling ===")
    
    urls = [
        "https://clickpay.cpi-outsourcing.com/",
        "https://facebook.com",
        "https://www.indeed.com",
        "https://www.google.com",
    ]
    
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun_many(
            urls=urls
        ) 

        print(f"Crawled {len(results)} URLs in parallel:")
        for i, result in enumerate(results):
            print(
                f" {1 + 1}. {result.url} - {'Success' if result.success else 'Failed'} and {len(result.markdown.raw_markdown)} chars"
            )
            # print(f"Context: {result.markdown.raw_markdown}")
            
async def demo_fit_markdown():
    print("\n=== 3. Fit markdown with LLM Content Filter ===")
    
    async with AsyncWebCrawler() as crawler:
        result: CrawlResult = await crawler.arun(
            url="https://clickpay.cpi-outsourcing.com/",
            # "https://en.wikipedia.org/wiki/Python_(programming_language)",
            config=CrawlerRunConfig(
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter()
                )
            )
        )
        
        print(f"Raw: {len(result.markdown.raw_markdown)} -> {result.markdown.raw_markdown}")
        print(f"Fit: {len(result.markdown.fit_markdown)} -> {result.markdown.fit_markdown}")
        
        
async def demo_llm_structured_no_schema():
    extraction_strategy = LLMExtractionStrategy(
        config=LLMConfig(
            provider="ollama/llama3.1",
            base_url="http://127.0.0.1:11434"
        ),
        instruction="This is news.ycombinator.com, extract all news, and for each, I want title, source url, number of comments",
        extract_type="schema",
        schema="{title: string, url: string, comments: number}",
        extra_args={
            "temperature": 0.0,
        },
        verbose=True
    )
    
    config = CrawlerRunConfig(extraction_strategy=extraction_strategy)
    
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            "https://news.ycombinator.com/",
            config=config
        )
        
        for result in results:
            print(f"URL: {result.url}")
            print(f"Success: {result.success}")
            if result.success:
                data = json.loads(result.extracted_content)
                print(json.dumps(data, indent=2))
            else:
                print("Failed to extract structured data")
            

async def demo_media_and_links():
    print("\n=== 8. Media and Links Extraction ===")
    
    browser_cfg = BrowserConfig(
        headless=False,  # Buksan ang browser para makita natin ang load state
        extra_args=["--disable-blink-features=AutomationControlled"] # Tinatanggal nito ang "WebDriver" flag na paboritong tingnan ng Google
    )

    run_cfg = CrawlerRunConfig(
        wait_for_images=True,
        delay_before_return_html=5.0,  # Bigyan natin ng 5 segundo para mag-render ang JS
        scan_full_page=True,           # Pipilitin nitong mag-scroll para mag-trigger ang image loaders
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results: List[CrawlResult] = await crawler.arun("https://en.wikipedia.org/wiki/Main_Page")
        # results: List[CrawlResult] = await crawler.arun(
        #     url="https://www.google.com/search?q=laptop&udm=28",
        #     config=run_cfg
        # )
        
        for i,result in enumerate(results):
            images = result.media.get("images", [])
            print(f"Found {len(images)} images")
            
            # Extract and save all links (internal external)
            internal_links = result.links.get("internal", [])
            external_links = result.links.get("external", [])
            
            print(f"Found {len(internal_links)} internal links")
            print(f"Found {len(external_links)} external links")
            
            for image in images[:3]:
                print(f"Image: {image['src']}")
            for link in internal_links[:3]:
                print(f"Internal link: {link['href']}")
            for link in external_links[:3]:
                print(f"External link: {link['href']}")
            
            
            with open("images.json", "w") as f:
                json.dump(images, f, indent=2)
            
            with open("links.json", "w") as f:
                json.dump(
                    {"internal": internal_links, "external": external_links},
                    f,
                    indent=2
                )

async def demo_screenshot_and_pdf():
    print("== 9. Screenshot and PDF capture ===")
    
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            url="https://clickpay.cpi-outsourcing.com/",
            # url="https://en.wikipedia.org/wiki/Giant_anteater",
            config=CrawlerRunConfig(screenshot=True, pdf=True, wait_for_images=True)
        ) 
        temp_dir = __cur_dir__ / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        for i, result in enumerate(results):
            if result.screenshot:
                screenshot_path = temp_dir / "example_screenshot.png"
                with open(screenshot_path, "wb") as f:
                    f.write(base64.b64decode(result.screenshot))
                print(f"Screenshot saved to {screenshot_path}")
                
            if result.pdf:
                pdf_path = temp_dir / "example.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(result.pdf)
                print(f"PDF saved to {pdf_path}")

async def main():
    print("... Comprehensive Crawl4AI Demo...")
    print("Note: Some examples require API keys or other configurations")
    
    # Run all codes
    # await demo_basic_crawl()
    # await demo_parallel_crawl()
    # await demo_fit_markdown()
    await demo_llm_structured_no_schema()
    # await demo_llm_css_structured_no_schema()
    # await demo_deep_crawl()
    # await demo_js_interaction()
    # await demo_media_and_links()
    # await demo_screenshot_and_pdf()
    # await demo_proxy_rotation()
    # await demo_raw_html_and_file()
    
    # Clean up any temp files that may have created
    print("\n === Demo Complete ===")
    print("Check for any generated files (screenshots, PDFs) in the current directory")
    
asyncio.run(main())