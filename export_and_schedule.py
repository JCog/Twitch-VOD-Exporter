import os
import sys
import time
from datetime import date, timedelta, datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from selenium import webdriver
from selenium.webdriver import FirefoxProfile, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


# arg1 = twitch username, arg2 = firefox profile path, arg3 = geckodriver path

def init_selenium():
    options = Options()
    options.add_argument('-headless')
    options.profile = FirefoxProfile(sys.argv[2])
    options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
    driver = webdriver.Firefox(service=Service(sys.argv[3]), options=options)
    return driver


def export_recent_vod(driver):
    print('Exporting most recent Twitch VOD to YouTube... ', end='')
    cs_date = ('div.iqUbUe:nth-child(1) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1) > div:nth-child(1) > '
               'div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > '
               'div:nth-child(1)')
    cs_hamburger = ('div.iqUbUe:nth-child(1) > div:nth-child(1) > div:nth-child(4) > div:nth-child(1) > '
                    'div:nth-child(1) > button:nth-child(1)')
    cs_export = 'div.jNrYjU:nth-child(6) > button:nth-child(1)'
    id_title = 'ye-title'
    cs_start_export = 'div.iiBsfk:nth-child(2) > button:nth-child(1)'

    driver.get(f'https://dashboard.twitch.tv/u/{sys.argv[1]}/content/video-producer')
    date_text = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, cs_date))).text
    date_converted = datetime.strptime(date_text, '%B %d, %Y').strftime('%#m/%#d/%y')
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, cs_hamburger))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, cs_export))).click()
    title = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_title)))
    titleText = title.get_attribute("value")
    title.clear()
    title.send_keys(f'Twitch VOD {date_converted} - {titleText}')
    driver.find_element(By.CSS_SELECTOR, cs_start_export).click()
    time.sleep(2)
    print('done')
    return date_converted


def draw_text(image, text, size, y_offset):
    font = ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf', size)
    x = image.width / 2
    y = image.height / 2
    transparent = (0, 0, 0, 0)
    white = (255, 255, 255)
    black = (0, 0, 0)
    stroke_width = 4
    ds_offset = 3

    # drop shadow
    ds_image = Image.new('RGBA', (image.width, image.height), transparent)
    ds_draw = ImageDraw.Draw(ds_image)
    ds_draw.text((x + ds_offset, y + ds_offset + y_offset), text, fill=black, align='center', font=font, anchor='mm',
                 stroke_fill=black, stroke_width=stroke_width)
    ds_image = ds_image.filter(ImageFilter.GaussianBlur(3))
    image.paste(ds_image, (0, 0), ds_image)

    # regular text
    draw = ImageDraw.Draw(image)
    draw.text((x, y + y_offset), text, fill=white, align='center', font=font, anchor='mm', stroke_fill=black,
              stroke_width=stroke_width)


def create_thumbnail(base, output, date_string):
    print('Creating thumbnail... ', end='')
    title = "JCog Twitch VOD"
    image = Image.open(base)
    draw_text(image, title, 120, -60)
    draw_text(image, date_string, 80, 60)
    image.save(output)
    print('done')


def schedule_video(driver, thumbnail_location, vod_date):
    print('Scheduling YouTube VOD...')
    id_content = 'menu-item-1'
    cs_top_row = ('ytcp-video-row.style-scope:nth-child(3) > div:nth-child(1) > div:nth-child(2) > '
                  'ytcp-video-list-cell-video:nth-child(1) > div:nth-child(2) > h3:nth-child(1) > a:nth-child(1) > '
                  'span:nth-child(1)')

    id_show_more = 'toggle-button'
    id_notify_subs = 'notify-subscribers'

    id_upload_tn = 'file-loader'

    cs_playlists = 'ytcp-video-metadata-playlists.style-scope'
    xp_playlist = "//*[contains(text(), 'Twitch VODs')]"
    cs_playlist_done = '.done-button > div:nth-child(3)'

    cs_visibility = 'ytcp-video-metadata-visibility.style-scope'
    id_schedule = 'second-container-expand-button'
    cs_date = '#datepicker-trigger > ytcp-dropdown-trigger:nth-child(1)'
    cs_date_input = '#input-2 > input:nth-child(1)'
    cs_time_input = 'input.tp-yt-paper-input'
    public_date = (date.today() + timedelta(days=1, hours=6)).strftime('%m/%d/%Y')
    public_time = '11:00 AM'
    id_visibility_done = 'save-button'

    id_save = 'save'
    xp_save_done = "//*[contains(text(), 'Changes saved')]"

    # navigate to video details
    driver.get('https://studio.youtube.com/')
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_content))).click()
    first_fail = True
    while True:
        top_row = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, cs_top_row)))
        recent_title = top_row.text
        if vod_date in recent_title:
            top_row.click()
            break

        if first_fail:
            print()
            first_fail = False
        print('Recent VOD not found, retrying in 30 seconds')
        time.sleep(30)
        driver.refresh()

    # edit video details
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_show_more))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_notify_subs))).click()

    # thumbnail
    driver.find_element(By.ID, id_upload_tn).send_keys(os.path.join(os.getcwd(), thumbnail_location))

    # playlist
    driver.find_element(By.CSS_SELECTOR, cs_playlists).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xp_playlist))).click()
    driver.find_element(By.CSS_SELECTOR, cs_playlist_done).click()

    # schedule
    driver.find_element(By.CSS_SELECTOR, cs_visibility).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_schedule))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, cs_date))).click()
    date_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, cs_date_input)))
    date_input.clear()
    date_input.send_keys(public_date)
    date_input.send_keys(Keys.RETURN)
    time_input = driver.find_element(By.CSS_SELECTOR, cs_time_input)
    time_input.clear()
    time_input.send_keys(public_time)
    time_input.send_keys(Keys.RETURN)
    driver.find_element(By.ID, id_visibility_done).click()

    # save
    driver.find_element(By.ID, id_save).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xp_save_done)))
    print('done')


def main():
    thumbnail_base = 'base.png'
    thumbnail_output = 'thumbnail.png'
    sel_driver = init_selenium()

    vod_date = export_recent_vod(sel_driver)
    create_thumbnail(thumbnail_base, thumbnail_output, vod_date)
    schedule_video(sel_driver, thumbnail_output, vod_date)

    sel_driver.close()


print("Export and Schedule script started")
main()
