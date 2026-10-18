import os
import requests

# 地點設定（以桃園市為例）
LOCATION_NAME = "桃園市"
LATITUDE = 24.9937
LONGITUDE = 121.3010


def get_weather_and_air_quality():
  """取得最高溫度、最高降雨機率與最高 AQI。"""
  # 1. 天氣預報 API
  weather_url = "https://api.open-meteo.com/v1/forecast"
  weather_params = {
      "latitude": LATITUDE,
      "longitude": LONGITUDE,
      "daily": ["temperature_2m_max", "precipitation_probability_max"],
      "timezone": "Asia/Taipei",
      "forecast_days": 1,
  }
  weather_resp = requests.get(weather_url, params=weather_params, timeout=30)
  weather_resp.raise_for_status()
  weather_data = weather_resp.json()

  forecast_date = weather_data["daily"]["time"][0]
  max_temp = weather_data["daily"]["temperature_2m_max"][0]
  max_rain_prob = weather_data["daily"]["precipitation_probability_max"][0]

  # 2. 空氣品質 API（改用 hourly 抓取 us_aqi 並計算當日最大值）
  air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
  air_params = {
      "latitude": LATITUDE,
      "longitude": LONGITUDE,
      "hourly": "us_aqi",
      "timezone": "Asia/Taipei",
      "forecast_days": 1,
  }
  air_resp = requests.get(air_url, params=air_params, timeout=30)
  air_resp.raise_for_status()
  air_data = air_resp.json()

  aqi_list = [v for v in air_data["hourly"]["us_aqi"] if v is not None]
  max_aqi = max(aqi_list) if aqi_list else 0

  return forecast_date, max_temp, max_rain_prob, max_aqi


def send_telegram(message):
  """發送 Telegram 訊息。"""
  bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
  chat_id = os.environ.get("TELEGRAM_CHAT_ID")

  if not bot_token or not chat_id:
    raise ValueError("未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID！")

  url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
  payload = {"chat_id": chat_id, "text": message}
  response = requests.post(url, json=payload, timeout=30)
  response.raise_for_status()


def main():
  try:
    forecast_date, max_temp, max_rain_prob, max_aqi = (
        get_weather_and_air_quality()
    )

    print(f"預報日期：{forecast_date}")
    print(f"地點：{LOCATION_NAME}")
    print(f"最高溫度：{max_temp}°C")
    print(f"最高降雨機率：{max_rain_prob}%")
    print(f"AQI 指數：{max_aqi}")

    # 多重條件判斷
    advice_list = []

    if max_rain_prob >= 60:
      advice_list.append("☔ 今日降雨機率較高，出門請攜帶雨傘。")

    if max_temp >= 33:
      advice_list.append("☀️ 氣溫偏高，請注意防曬並多補充水分。")

    if max_aqi >= 100:
      advice_list.append("😷 空氣品質較差 (AQI >= 100)，建議配戴口罩。")

    if not advice_list:
      advice_text = "✅ 各項指標良好，今日非常適合外出通勤！"
    else:
      advice_text = "\n".join(advice_list)

    message = (
        f"🚨【智慧通勤風險通知】🚨\n\n"
        f"📅 日期：{forecast_date}\n"
        f"📍 地點：{LOCATION_NAME}\n"
        f"🌡️ 最高溫度：{max_temp}°C\n"
        f"🌧️ 降雨機率：{max_rain_prob}%\n"
        f"🌫️ 空氣品質 AQI：{max_aqi}\n\n"
        f"💡 通勤建議：\n{advice_text}"
    )

    is_force = os.getenv("FORCE_SEND", "false").lower() == "true"
    if is_force:
      message += "\n\n(此訊息為手動測試發送)"

    send_telegram(message)
    print("Telegram 通勤風險通知傳送成功！")

  except Exception as e:
    print(f"執行失敗：{e}")
    raise e


if __name__ == "__main__":
  main()
