from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import html5lib
import time
import datetime

def format_rows(rows):
    df = pd.DataFrame(rows)
    df.columns = ['Time', 'Book', 'Away Team', 'Home Team']
    books = ['Pinnacle', 'RedZone']
    
    df = df[df['Book'].isin(books)]
    
    tmp = df["Home Team"].str.split(" ", expand=True)
    df['Home Line'] = tmp[0]
    df['Home Odds'] = tmp[1]
    tmp = df["Away Team"].str.split(" ", expand=True)
    df['Away Line'] = tmp[0]
    df['Away Odds'] = tmp[1]

    header_raw = driver.find_elements_by_xpath("//div[@class='SortableTable__header']//div[@class='SortableTable__header-row']")
    for x in range(len(header_raw)):
        header = header_raw[0].text.split('\n')

    df['Away Team'] = header[2]
    df['Home Team'] = header[3]

    # Only find the scores for the game including the current team
    if header[2].split(' ')[-1] == 'Clippers':
        scores_raw = driver.find_elements_by_xpath("//div[@class='lines-teams-container']//a[contains(@href,'{}')]//div[@class='team-score']".format('LA'))
    else:
        scores_raw = driver.find_elements_by_xpath("//div[@class='lines-teams-container']//a[contains(@href,'{}')]//div[@class='team-score']".format(header[2].split(' ')[0]))
    df['Home Score'] = int(scores_raw[1].text)
    df['Away Score'] = int(scores_raw[0].text)

    # Change the lines and odds to integers
    df['Home Line'] = df['Home Line'].str.replace('½','.5')
    df['Away Line'] = df['Away Line'].str.replace('½','.5')
    df['Home Line Open'] = df['Home Line'].iloc[-1]
    df['Away Line Open'] = df['Away Line'].iloc[-1]

    # Final formatting and changing column data types to numeric
    df['Home Line'].replace('PK', '0', inplace=True)
    df['Away Line'].replace('PK', '0', inplace=True)
    df['Home Odds'].replace('PK', '-110', inplace=True)
    df['Away Odds'].replace('PK', '-110', inplace=True)
    df['Home Odds'].replace('--', '-110', inplace=True)
    df['Away Odds'].replace('--', '-110', inplace=True)
    df['Home Line Open'].replace('PK', '0', inplace=True)
    df['Away Line Open'].replace('PK', '0', inplace=True)
    df['Home Line'] = pd.to_numeric(df['Home Line'])
    df['Away Line'] = pd.to_numeric(df['Away Line'])
    df['Home Line Open'] = pd.to_numeric(df['Home Line Open'])
    df['Away Line Open'] = pd.to_numeric(df['Away Line Open'])
    df['Home Odds'] = pd.to_numeric(df['Home Odds'])
    df['Away Odds'] = pd.to_numeric(df['Away Odds'])

    # Export to .csv
    file = 'games/'+df["Away Team"].iloc[0] +'@' +  df["Home Team"].iloc[0] + ' ' + driver.current_url.split("/")[-1] +'.csv'
    file = file.replace(' ', '_')
    df.to_csv(file, index=False)
    print("Saving file: {}".format(file))



webdriver = "chromedriver_win32/chromedriver.exe"
driver = Chrome(webdriver)
driver.fullscreen_window()

start_date = "2020-03-12"
start_d = datetime.datetime.strptime(start_date,"%Y-%m-%d")
#start_d = datetime.datetime.today()
#start_date = start_d.strftime("%Y-%m-%d")
end_d = start_d - datetime.timedelta(days=1)
end_date = end_d.strftime("%Y-%m-%d")
#end_date = "2020-02-22"

while start_date != end_date:
    try:
        my_url = "https://therundown.io/odds/nba/{}".format(start_date)
        driver.get(my_url)
        time.sleep(12)

        # click the tab to only show live data
        driver.find_element_by_xpath("//div[text() = 'Live']").click()
        # Find the ellipses button for each game and click it to expand the graphs view
        elps_buttons = driver.find_elements_by_class_name("glyphicon.glyphicon-option-horizontal")

        for btn in elps_buttons[1:]:
            btn.click()
            time.sleep(12)

            # Click the tables button to show the data in table format instead of graph
            # The webpage wont let us click the button if it is not in view, so first we scroll to the button
            graph_button = driver.find_element_by_xpath("//ul[@class='ReactTabs__TabList']//li[not(contains(@class,'ReactTabs__Tab--selected'))]")
            coordinates = graph_button.location_once_scrolled_into_view # returns dict of X, Y coordinates
            driver.execute_script('window.scrollTo({}, {});'.format(coordinates['x'], coordinates['y']))
            graph_button.click()
            time.sleep(12)

            actions = ActionChains(driver)
            actions.send_keys(Keys.ARROW_DOWN)

            # Select the table so we can scroll down properly
            table = driver.find_element_by_xpath("//div[@class='SortableTable__body']")
            scroll_to = ActionChains(driver)
            scroll_to.move_to_element(table).perform()
            table.click()
            time.sleep(1)
            table.click()

            rows = []
            # We will only get the odds from the first record to 3 hours back
            time_raw = driver.find_elements_by_xpath("//div[@class='SortableTable__body']//div[@class='SortableTable__row']")[0].text.split('\n')[0]
            curr_time = time.mktime(time.strptime(time_raw+" 20", '%m/%d %I:%M:%S %p %y'))
            end_time = curr_time - (60*60*3) # 3 hours
            try:
                while curr_time > end_time:
                    rows_raw = driver.find_elements_by_xpath("//div[@class='SortableTable__body']//div[@class='SortableTable__row']")
                    for x in range(len(rows_raw)):
                        arr = rows_raw[x].text.split('\n')
                        if arr not in rows:
                            rows.append(arr)

                    curr_time = time.mktime(time.strptime(arr[0]+" 20", '%m/%d %I:%M:%S %p %y'))
                    # scroll the table
                    for x in range(7):
                        actions.perform()
            except:
                pass

            format_rows(rows)
            btn.click()

    except Exception as e:
        print("Error: {}".format(e))
        # if an error occurs, re-open the page and try again
        driver.quit()
        webdriver = "chromedriver_win32/chromedriver.exe"
        driver = Chrome(webdriver)
        driver.fullscreen_window()
    else:
        # we only want to change the start date if there were no errors
        start_d = start_d - datetime.timedelta(days=1)
        start_date = start_d.strftime("%Y-%m-%d")

print("All done")
driver.quit()