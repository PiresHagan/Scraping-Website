from bs4 import BeautifulSoup
import requests
import os
import os.path
import csv
import time
from urllib.parse import quote

print()
print("========== Web Scraping Data From ocsn.net =============")
print()
print("Limit by Case Date Range (ex: MM/DD/YYYY - 01/01/2010)")
start_date = input("Cases Filed After Date: ")
end_date = input("Cases Filed Before Date: ")
encoded_start_date = quote(start_date, safe='')
encoded_end_date = quote(end_date, safe='')
data = []
table_data = []
scrapped_table = None
scraping_stopped = 0
host_url = "https://www.oscn.net"
base_url = "https://www.oscn.net/dockets/"
list_query = "Results.aspx?db=all&number=&lname=&fname=&mname=&DoBMin=&DoBMax=&partytype=&apct=&dcct=2&FiledDateL=" + encoded_start_date + "&FiledDateH=" + encoded_end_date + "&ClosedDateL=&ClosedDateH=&iLC=&iLCType=&iYear=&iNumber=&citation="
# list_query = "Results.aspx?db=all&number=&lname=&fname=&mname=&DoBMin=&DoBMax=&partytype=&apct=&dcct=2&FiledDateL=10%2F06%2F2023&FiledDateH=12%2F06%2F2023&ClosedDateL=&ClosedDateH=&iLC=&iLCType=&iYear=&iNumber=&citation="

list_url = base_url + list_query
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_row_detail(base_url, result_rows):
    global table_data
    table_data = []
    for html_tr in result_rows:
        case_number = html_tr.find("td", class_ = "result_casenumber").getText().strip()
        date_filed = html_tr.find("td", class_ = "result_datefiled").getText().strip()
        party_list = ''
        issue_text = ''
        is_foreclousure = ''
        detail_link = base_url + html_tr.find("a")['href']
        response_detail = requests.get(detail_link, headers=headers)
        try:
            while response_detail.status_code != 200:
                print("Refresh the website on the browser")
                time.sleep(5)
                response_detail = requests.get(detail_link, headers=headers)
            soup = BeautifulSoup(response_detail.content, 'html.parser')
            if soup.find('h2', class_ = 'section party') != None:
                party_html = soup.find('h2', class_ = 'section party').find_next_sibling()
                for sub_element in list(party_html.children):
                    sub_element_str = sub_element.get_text().strip()
                    party = ''
                    if len(sub_element_str):
                        for line in sub_element_str.split('\n'):
                            if len(line):
                                party += line.strip() + " "
                        party = party.replace(u'\xa0', u' ')
                        party_list += party + "\n"
                
            if soup.find('h2', class_ = 'section issues') :
                issue_html = soup.find('h2', class_ = 'section issues').find_next_sibling()
                while issue_html.name != 'h2':
                    issue_text += issue_html.get_text().strip()
                    issue_html = issue_html.find_next_sibling()
            if issue_text.find("FORECLOSURE") != -1:
                is_foreclousure = "foreclousure"
            
            print(case_number)
            table_data.append([case_number, date_filed, party_list, issue_text, is_foreclousure, detail_link])
        except :
            print('error is issued')
    # return table_data
def table_scraping(table_list):
    global scrapped_table, data, scraping_stopped
    try:
        for table in table_list:
            if scraping_stopped == 1:
                if scrapped_table == table:
                    scraping_stopped = 0
                    pass
                else:
                    pass
            else:                
            #     pass
            # else:
                table_name = table.find("caption", class_="caseCourtHeader").contents[0]
                print(table_name.upper(), "************")
                if table.find("td", class_="moreResults") != None:
                    list_url = host_url + table.find("td", class_="moreResults").a["href"]
                    response = requests.get(list_url, headers=headers)
                    while response.status_code != 200:
                        print("Refresh the website on the browser")
                        time.sleep(5)
                        response = requests.get(list_url, headers=headers)
                    html_content = response.content
                    soup = BeautifulSoup(html_content, 'html.parser')
                    row_list = soup.find_all("tr", class_="resultTableRow")
                    get_row_detail(base_url, row_list)
                else:
                    row_list = table.find_all("tr", class_="resultTableRow")
                    get_row_detail(base_url, row_list)
                data = data + table_data
                scrapped_table = table
        filename = start_date.replace(u'/', u'-') + "-" + end_date.replace(u'/', u'-') + ".csv"
        if os.path.exists(filename):
            os.remove(filename)
        with open(filename, 'w', newline='', encoding='utf-8') as toWrite:
            writer = csv.writer(toWrite)
            writer.writerows(data)
    except:
        scraping_stopped = 1
        print("The error is occured")
        print("Completed ", scrapped_table.find("caption", class_="caseCourtHeader").contents[0].upper())
        print("Trying to continue scrping 15 seconds later")
        print("Press 'Ctrl + C' to stop scraping.")
        time.sleep(15)
        # print(len(data))
        table_scraping(table_list)

def main(list_url):
    try:
        response = requests.get(list_url, headers=headers)
        while response.status_code != 200:
            print("Refresh the website on the browser")
            time.sleep(5)
            response = requests.get(list_url, headers=headers)
        print()
        print("Scraping started")
        print()
        html_content = response.content
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        table_list = soup.find_all(class_="caseCourtTable")
        table_scraping(table_list)
    except:
        print("Confirm your internet connection.")
        print("Trying to connect the internet 15 seconds later")
        time.sleep(15)
        main(list_url)
main(list_url)

