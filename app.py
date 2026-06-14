import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def run_automation():
    username = os.getenv("PAYSLIP_USERNAME")
    password = os.getenv("PAYSLIP_PASSWORD")
    click_pay_link = os.getenv("WEBSITE")
    
    print(f"Username: {username}")
    print(f"PASSWORD: {password}")
    print(f"Click Pay: {click_pay_link}")
    
    # Browser crawl
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        await page.goto(click_pay_link)
        
        await page.fill('#username', username)
        await page.fill('#password', password)
        await page.click('#loginbutton')
        await page.click('#ico_payroll')
        
        await page.wait_for_load_state("networkidle")

async def  main():
    await run_automation()



if __name__ == "__main__":
    asyncio.run(main())