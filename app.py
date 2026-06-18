import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import pandas as pd
from openpyxl.workbook import Workbook
import smtplib 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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
        browser = await playwright.chromium.launch(headless=True)
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
        
        total_earnings =  df_earnings["Total Amount"].astype(str).str.replace(',','', regex=True).astype(float).sum()
        print(f"Total Earnings: {total_earnings:,.2f}")

        # use the actual deductions column name created above ("Amount")
        total_deductions = df_deductions["Amount"].astype(str).str.replace(',','', regex=True).astype(float).sum()
        print(f"Total Deductions: {total_deductions:,.2f}")
        
        net_pay = total_earnings - total_deductions
        print(f"Net Pay: {net_pay:,.2f}")
        
        excel_file = "Payslip_Summary.xlsx"
        
        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            df_earnings.to_excel(writer, sheet_name="Earnings", index=False)
            df_deductions.to_excel(writer, sheet_name="Deduction", index=False)
        
            df_summary = pd.DataFrame({
                "Category": ["Total Earnings", "Total Deductions", "Net Pay"],
                "Amount": [total_earnings, total_deductions, net_pay]
            })
            
            df_summary.to_excel(writer, sheet_name="Summary", index=False)
        print(f"Excel file saved as: {excel_file}")
        
        
        sender_email = os.getenv("EMAIL_SENDER")
        print(sender_email)
        sender_password = os.getenv("EMAIL_PASSWORD")
        receiver_email = os.getenv("EMAIL_RECEIVERS")
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"Payslip Summary Report - Net Pay: PHP {net_pay:,.2f}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #f9f9f9;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 0;">
                    📊 Payslip Automation Report
                </h2>
                <p>Magandang araw! Narito ang buod ng iyong payslip na awtomatikong nakuha ng system:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <tr style="background-color: #2c3e50; color: white;">
                        <th style="padding: 12px; text-align: left;">Kategorya</th>
                        <th style="padding: 12px; text-align: right;">Halaga (PHP)</th>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee; color: #27ae60; font-weight: bold;">Total Earnings</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; color: #27ae60; font-weight: bold;">{total_earnings:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee; color: #c0392b; font-weight: bold;">Total Deductions</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; color: #c0392b; font-weight: bold;">-{total_deductions:,.2f}</td>
                    </tr>
                    <tr style="background-color: #ecf0f1; font-size: 1.1em;">
                        <td style="padding: 12px; color: #2980b9; font-weight: bold;">NET PAY</td>
                        <td style="padding: 12px; text-align: right; color: #2980b9; font-weight: bold; border-left: 2px solid #2980b9;">{net_pay:,.2f}</td>
                    </tr>
                </table>
                
                <p style="font-size: 0.9em; color: #7f8c8d;">
                    *Nakalakip sa email na ito ang buong detalye (Earnings at Deductions breakdown) sa loob ng Excel file.
                </p>
                <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #e0e0e0; font-size: 0.8em; color: #95a5a6; text-align: center;">
                    Fin-Ops Automation Bot • Do not reply to this email.
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            with open(excel_file, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {excel_file}",
                )
                msg.attach(part)
                
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
                
            print("Email successfully sent with Excel attachment!")
        except Exception as e:
            print(f"Failed to send email: {e}")
async def  main():
    await run_automation()



if __name__ == "__main__":
    asyncio.run(main())