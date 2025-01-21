import requests
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

# استبدل بـ API Token الخاص بك من Telegram
API_TOKEN = '8019566370:AAEbI46RB0EJPluJtV_E-amP53ur1IF5nXc'
# استبدل بـ معرف القناة الخاص بك (يبدأ ب @)
CHANNEL_ID = '@Trump2Price'

# إنشاء كائن البوت
bot = Bot(token=API_TOKEN)

# دالة لجلب سعر العملة من Binance API
def get_trump_price():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    parameters = {
        'symbol': 'TRUMPUSDT'  # رمز العملة (تأكد من أنه صحيح)
    }
    try:
        # إرسال طلب إلى Binance API
        response = requests.get(url, params=parameters, timeout=10)
        response.raise_for_status()  # التحقق من وجود أخطاء في الطلب
        data = response.json()
        return {
            'price': float(data['lastPrice']),  # السعر الأخير
            'change': float(data['priceChangePercent']),  # نسبة التغير (24 ساعة)
            'high': float(data['highPrice']),  # أعلى سعر (24 ساعة)
            'low': float(data['lowPrice']),  # أدنى سعر (24 ساعة)
            'volume': float(data['volume'])  # حجم التداول (24 ساعة)
        }
    except requests.exceptions.RequestException as e:
        print(f"خطأ في الاتصال بالـ API: {e}")
        return None

# دالة لجلب السعر قبل دقيقة واحدة
def get_price_1m_ago():
    url = "https://api.binance.com/api/v3/klines"
    parameters = {
        'symbol': 'TRUMPUSDT',  # رمز العملة
        'interval': '1m',       # الفاصل الزمني (1 دقيقة)
        'limit': 2              # عدد النقاط (2 نقطة: الآن وقبل دقيقة)
    }
    try:
        response = requests.get(url, params=parameters, timeout=10)
        response.raise_for_status()
        data = response.json()
        # سعر الإغلاق قبل دقيقة واحدة
        old_price = float(data[0][4])  # سعر الإغلاق قبل دقيقة
        new_price = float(data[1][4])  # سعر الإغلاق الحالي
        # حساب نسبة التغير
        change = ((new_price - old_price) / old_price) * 100
        return change
    except requests.exceptions.RequestException as e:
        print(f"خطأ في الاتصال بالـ API: {e}")
        return None

# دالة لإرسال السعر إلى القناة
async def send_price_to_channel():
    data = get_trump_price()
    if data:
        price = data['price']
        change = data['change']
        high = data['high']
        low = data['low']
        volume = data['volume']

        # تحديد الاتجاه (صعود أو هبوط)
        if change > 0:
            trend = "Up"
            emoji = "🟩"
        else:
            trend = " down "
            emoji = "🟥"

        # جلب نسبة التغير خلال الدقيقة الأخيرة
        change_1m = get_price_1m_ago()
        if change_1m is not None:
            change_1m_text = f" (Change): **{change_1m:.2f}%**\n"
        else:
            change_1m_text = "تعذر الحصول على نسبة التغير (الدقيقة الأخيرة).\n"

        # إعداد الرسالة الأولى (سعر العملة)
        price_message = f"TRUMP: **${price:,.4f}** \n | {emoji}"

        # إرسال الرسالة الأولى إلى القناة
        sent_message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=price_message,
            parse_mode=ParseMode.MARKDOWN
        )

        # إعداد الرسالة الثانية (التفاصيل الإضافية)
        details_message = (
            f"{trend}\n"
            f"🕘 {change_1m_text}"
            f" :↗️ **${high:,.1f}** \n"
            f":↘️ **${low:,.1f}**\n"
            f"👥: **{volume:,.1f} **\n"
        )

        # إرسال الرسالة الثانية كرد على الرسالة الأولى
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=details_message,
            reply_to_message_id=sent_message.message_id,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        print("تعذر الحصول على سعر العملة. تحقق من الاتصال بالإنترنت أو الـ API.")

# الدالة الرئيسية لتشغيل البوت
async def main():
    while True:
        await send_price_to_channel()  # إرسال السعر
        await asyncio.sleep(60)  # انتظر 60 ثانية (دقيقة واحدة)

# تشغيل البوت
if __name__ == "__main__":
    asyncio.run(main())  # تشغيل الدالة الرئيسية بشكل غير متزامن 
