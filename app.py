import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import pandas as pd

load_dotenv()

async def run_automation():
    username = os.getenv("PAYSLIP_USERNAME")
    password = os.getenv("PAYSLIP_PASSWORD")
    click_pay_link = os.getenv("WEBSITE")
    
    # print(f"Username: {username}")
    # print(f"PASSWORD: {password}")
    # print(f"Click Pay: {click_pay_link}")
    
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
        
        
        
        table_raw_data = await page.get_by_role("table").all_inner_texts() 
        
        clean_lines = []
        
        for block in table_raw_data:
            lines = block.split('\n')
            for line in lines:
                cleaned = line.strip()
                if cleaned and cleaned not in clean_lines:
                    clean_lines.append(cleaned)
        
        # print(clean_lines)

        #Description\tHrs.\tAmount
        # print(clean_lines.index("Description\tAmount"))
        earnings_starting_index = clean_lines.index("Description\tHrs.\tAmount") + 1 
        earnings_last_index = clean_lines.index("Description\tAmount") 
        
        deductions_starting_index = clean_lines.index("Description\tAmount") + 1
        deductions_last_index = clean_lines.index("Total Taxable Income\t41,636.20\tTotal Deductions\t8,184.00")
        # deductions_last_index = clean_lines.index("Non-taxable\t0.00")
        # print(clean_lines[deductions_starting_index])
        # print(clean_lines[deductions_last_index])
        
        # print(clean_lines[earnings_starting_index])
        # print(clean_lines[earnings_last_index])
        

        
        earnings_raw = clean_lines[earnings_starting_index:earnings_last_index]
        deductions_raw = clean_lines[deductions_starting_index:deductions_last_index]
        
        # print(f"Earnings: {earnings_raw}")
        # print()
        # print(f"Deductions: {deductions_raw}")
        
        # EARNING DATA FRAME
        earnings_data = []
        
        for item in earnings_raw:
            parts = [p.strip() for p in item.split("\t") if p.strip()]
            if len(parts) == 2:
                earnings_data.append([parts[0], 1, parts[1], parts[1] ])
            elif len(parts) == 3:
                clean_amount = parts[2].replace(',', '')
                earnings_data.append([parts[0], parts[1], float(clean_amount)/float(parts[1]), parts[2]])
                
        # print(earnings_data)
        df_earnings = pd.DataFrame(earnings_data, columns=["Description", "Hrs", "Unit Amount", "Total Amount"])
        
        print("=== EARNING DATAFRAME ===")
        print(df_earnings)
        print()
        
        deductions_data = []
        
        for item in deductions_raw:
            parts = [p.strip() for p in item.split("\t") if p.strip()]
            # print(len(parts))
            # print(parts)
            deductions_data.append(parts)
        
        # print(deductions_data)
        df_deductions = pd.DataFrame(deductions_data, columns=["Description", "Amount"])
        print("=== DEDUCTIONS DATAFRAME ===")
        print(df_deductions)
        print()
        

async def  main():
    await run_automation()



if __name__ == "__main__":
    asyncio.run(main())