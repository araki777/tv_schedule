import requests
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
from datetime import datetime, timedelta

# .envファイルの読み込み
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def line_notify(message):
  line_notify_token = os.getenv("LINE_TOKEN")
  line_notify_api = "https://notify-api.line.me/api/notify"
  headers = {"Authorization": f"Bearer {line_notify_token}"}
  data = {"message": f'{message}'}
  try:
      response = requests.post(line_notify_api, data=data, headers=headers)
      response.raise_for_status()
      logging.info(f"LINE Notify response: {response.text}")
  except requests.exceptions.RequestException as e:
      logging.error(f"Failed to send LINE notification: {e}")


def get_next_week_dates():
    today = datetime.today()
    return [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(7)]


def get_channels(driver):
  channel_element = driver.find_elements(By.CSS_SELECTOR, "div #ch_area ul li p")
  return [channel.text for channel in channel_element]


def format_time(time_str):
    # 時間文字列をフォーマットする
    return f"{time_str[8:10]}:{time_str[10:12]}"


def load_existing_entries(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return file.read().strip().split("\n")
    return []


def main():
    logging.info("Python timer trigger function started.")

      # chromeドライバのオプションを設定
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.getenv("CHROME_BINARY_PATH")  # もしくは Chrome ブラウザの実行ファイルのパスを指定
    chrome_options.add_argument("--headless")  # ヘッドレスモードで起動する場合
    chrome_options.add_argument("--no-sandbox")  # セキュリティ対策のためのオプション

    # Chromeドライバーのパスを指定
    chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")

    # Chromeドライバーを起動するためのサービスを設定
    chrome_service = webdriver.chrome.service.Service(chrome_driver_path)

    # Chromeドライバーを起動
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    # 今日から1週間分for文で回す
    next_week_dates = get_next_week_dates()

    # フィルタリングするタイトルを環境変数から取得
    filter_titles_str = os.getenv("TARGET_TV", "")
    filter_titles = [title.strip() for title in filter_titles_str.split(",")]

    # 既存のエントリを読み込む
    existing_entries = load_existing_entries("tv_schedule.txt")

    programs = []
    for date in next_week_dates:
      # ページ情報の取得
      url = os.getenv("TV_SCHEDULE_PAGE_PATH") + "broad_cast_date=" + date + "&ggm_group_id=" + os.getenv("TV_SCHEDULE_AREA")
      driver.get(url)

      # ページが完全に読み込まれるまで待機
      driver.implicitly_wait(10) # 最大10秒まで待機

      # チャンネル名の取得
      channels = get_channels(driver)

      # seleniumで番組情報を取得
      program_line_elements = driver.find_elements(By.CSS_SELECTOR, "[id^='program_line_']")

      for program_line in program_line_elements:
        # チャンネルIDを取得
        channel_id = program_line.get_attribute("id").replace("program_line_", "")
        channel_name = channels[int(channel_id) - 1] # チャンネル名を取得

        # seleniumで番組情報を取得
        sc_elements = program_line.find_elements(By.CSS_SELECTOR, ".sc-future, .sc-current, .sc-past")

        for sc_element in sc_elements:
          try:
              start_time = sc_element.get_attribute("s")
              end_time = sc_element.get_attribute("e")
              program_id = sc_element.get_attribute("pid")

              # プログラムタイトルと詳細を取得
              title = sc_element.find_element(By.CLASS_NAME, "program_title").text
              detail = sc_element.find_element(By.CLASS_NAME, "program_detail").text

              # タイトルがフィルタリング対象に含まれているかチェック
              if any(filter_title in title for filter_title in filter_titles):
                start_datetime = datetime.strptime(start_time, "%Y%m%d%H%M")
                formatted_start_time = format_time(start_time)
                formatted_end_time = format_time(end_time)

                program_info = (
                    f"{start_datetime.strftime('%m/%d')} {formatted_start_time}~{formatted_end_time} 【{channel_id} {channel_name}】    {title} {detail} [{program_id}]"
                )

                if program_info not in existing_entries:
                    programs.append(program_info)

          except Exception as e:
              logging.error(f"Error retrieving program details: {e}")

    # Chromeドライバーを閉じる
    driver.quit()

    if programs:
        # 結果をフォーマットしてファイルに追記する
        result_message = "\n".join(programs)

        with open("tv_schedule.txt", "a", encoding="utf-8") as file:
            file.write(result_message + "\n")

        # LINE に通知
        line_notify(result_message)

    logging.info("Python timer trigger function finished.")

if __name__ == "__main__":
    main()