import telebot
import requests
import time
import os
import random
from telebot import types
import json
from datetime import datetime, timedelta

# Токен бота (получить у @BotFather)
BOT_TOKEN = "8664701331:AAEWigbAkkrbJC3jHP1cIO-p7tNUh_6MOIw"  # Бесплатно

# Бесплатные API для генерации видео
FREE_APIS = {
    # Модели на Hugging Face (нужен бесплатный токен)
    "modelscope": "https://api-inference.huggingface.co/models/damo-vilab/modelscope-damo-text-to-video",
    "zeroscope": "https://api-inference.huggingface.co/models/cerspense/zeroscope_v2_576w",
    "text2video": "https://api-inference.huggingface.co/models/ali-vilab/text-to-video",
}

# Получите бесплатный токен на huggingface.co (регистрация бесплатная)
HF_TOKEN = "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"  # Замените на ваш токен

bot = telebot.TeleBot(8664701331:AAEWigbAkkrbJC3jHP1cIO-p7tNUh_6MOIw)

# Хранилище для пользователей (в реальном проекте используйте БД)
users_db = {}

class FreeVideoGenerator:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        self.daily_limit = 5  # Бесплатных видео в день
        self.queue = []
    
    def generate_with_huggingface(self, prompt, user_id):
        """Бесплатная генерация через Hugging Face"""
        
        # Проверяем лимиты
        if not self.check_limits(user_id):
            return "limit"
        
        try:
            # Выбираем случайную модель
            model_url = random.choice(list(FREE_APIS.values()))
            
            # Параметры запроса
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_frames": 8,  # Меньше кадров = быстрее и бесплатнее
                    "fps": 4,
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5
                }
            }
            
            # Отправляем запрос
            response = requests.post(
                model_url,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                # Сохраняем видео
                filename = f"videos/user_{user_id}_{int(time.time())}.mp4"
                os.makedirs("videos", exist_ok=True)
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                return filename
            elif response.status_code == 503:
                # Модель загружается
                return "loading"
            else:
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def generate_demo_video(self, prompt, user_id):
        """Создает простое демо-видео если API не работает"""
        import cv2
        import numpy as np
        
        filename = f"videos/demo_{user_id}_{int(time.time())}.mp4"
        os.makedirs("videos", exist_ok=True)
        
        # Создаем простое видео с текстом
        fps = 10
        duration = 3  # секунды
        frame_count = fps * duration
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, fps, (512, 512))
        
        for i in range(frame_count):
            # Создаем красивый фон
            frame = np.zeros((512, 512, 3), dtype=np.uint8)
            
            # Градиентный фон
            for y in range(512):
                color = int(255 * (y / 512))
                frame[y, :] = [color, color, 255]
            
            # Анимированный круг
            x = int(256 + 200 * np.sin(i * 0.5))
            y = int(256 + 150 * np.cos(i * 0.5))
            cv2.circle(frame, (x, y), 30, (0, 255, 0), -1)
            
            # Текст
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, "FREE VIDEO", (150, 100), font, 1, (255,255,255), 2)
            cv2.putText(frame, prompt[:30], (150, 200), font, 0.7, (255,255,255), 1)
            
            out.write(frame)
        
        out.release()
        return filename
    
    def check_limits(self, user_id):
        """Проверяет дневной лимит пользователя"""
        today = datetime.now().date()
        
        if user_id not in users_db:
            users_db[user_id] = {
                'count': 0,
                'date': today,
                'total': 0
            }
        
        user_data = users_db[user_id]
        
        # Сбрасываем счетчик если новый день
        if user_data['date'] != today:
            user_data['count'] = 0
            user_data['date'] = today
        
        # Проверяем лимит
        if user_data['count'] >= self.daily_limit:
            return False
        
        return True
    
    def increment_usage(self, user_id):
        """Увеличивает счетчик использований"""
        users_db[user_id]['count'] += 1
        users_db[user_id]['total'] += 1

# Создаем экземпляр генератора
generator = FreeVideoGenerator()

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = """
🎬 **Бесплатный Sora Video Bot** 🤖

**Совершенно бесплатно!** Никаких платежей!

🌟 **Что я умею:**
• Создавать видео по тексту
• 5 видео бесплатно каждый день
• Разные стили и эффекты

📋 **Команды:**
/create - создать видео
/limits - проверить лимиты
/help - помощь
/examples - примеры

🚀 **Начни прямо сейчас!**
    """
    
    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🎬 Создать видео"),
        types.KeyboardButton("📊 Мои лимиты"),
        types.KeyboardButton("❓ Помощь")
    )
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['create'])
@bot.message_handler(func=lambda m: m.text == "🎬 Создать видео")
def create_video(message):
    # Проверяем лимиты
    if not generator.check_limits(message.from_user.id):
        reset_time = datetime.now() + timedelta(days=1)
        bot.send_message(
            message.chat.id,
            f"❌ **Лимит на сегодня исчерпан!**\n\n"
            f"Вы использовали 5 из 5 бесплатных видео.\n"
            f"Лимит сбросится в {reset_time.strftime('%H:%M')} завтра.\n\n"
            f"Приходите завтра за новыми видео! 😊",
            parse_mode='Markdown'
        )
        return
    
    # Показываем настройки
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🖼 Обычное", callback_data="style_normal"),
        types.InlineKeyboardButton("🎨 Аниме", callback_data="style_anime"),
        types.InlineKeyboardButton("🎮 3D", callback_data="style_3d")
    )
    
    msg = bot.send_message(
        message.chat.id,
        "🎨 **Выбери стиль видео:**",
        parse_mode='Markdown',
        reply_markup=markup
    )
    
    # Сохраняем состояние
    bot.register_next_step_handler(msg, get_prompt)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("style_"):
        style = call.data.replace("style_", "")
        
        # Сохраняем стиль
        users_db[call.from_user.id] = users_db.get(call.from_user.id, {})
        users_db[call.from_user.id]['style'] = style
        
        bot.edit_message_text(
            f"✅ Выбран стиль: {style}\n\n"
            "✏️ **Теперь опиши видео:**\n\n"
            "Например:\n"
            "• мистор блинчик дрочит на фембоев\n"
            "• выебите меня\n"
            "• трахеите меня глубоко чтобы я стонал как последняя сука",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        
        # Ждем текст
        bot.register_next_step_handler(call.message, process_video)

def get_prompt(message):
    bot.send_message(
        message.chat.id,
        "✏️ **Опиши видео:**\n\n"
        "Чем подробнее, тем лучше результат!",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_video)

def process_video(message):
    prompt = message.text
    user_id = message.from_user.id
    style = users_db.get(user_id, {}).get('style', 'normal')
    
    # Добавляем стиль к промпту
    style_prompts = {
        'anime': f"{prompt}, anime style, vibrant colors",
        '3d': f"{prompt}, 3D render, pixar style",
        'normal': prompt
    }
    
    full_prompt = style_prompts.get(style, prompt)
    
    # Отправляем статус
    status_msg = bot.send_message(
        message.chat.id,
        "🔄 **Создаю видео...**\n"
        "⏳ Это займет 30-60 секунд\n"
        "✨ Использую бесплатные нейросети",
        parse_mode='Markdown'
    )
    
    # Генерируем видео
    video_path = generator.generate_with_huggingface(full_prompt, user_id)
    
    if video_path == "limit":
        bot.edit_message_text(
            "❌ Лимит на сегодня исчерпан!",
            message.chat.id,
            status_msg.message_id
        )
    elif video_path == "loading":
        # Если API загружается, создаем демо
        video_path = generator.generate_demo_video(full_prompt, user_id)
        
        if video_path:
            # Отправляем видео
            with open(video_path, 'rb') as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption=f"✅ **Видео готово!** (демо-режим)\n\n"
                            f"*Запрос:* {prompt}\n"
                            f"*Стиль:* {style}\n\n"
                            f"⚡ Бесплатно • {users_db[user_id]['count']+1}/5",
                    parse_mode='Markdown'
                )
            
            # Увеличиваем счетчик
            generator.increment_usage(user_id)
            
            # Удаляем статус
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            # Удаляем файл
            os.remove(video_path)
    elif video_path:
        # Отправляем видео
        with open(video_path, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=f"✅ **Видео готово!**\n\n"
                        f"*Запрос:* {prompt}\n"
                        f"*Стиль:* {style}\n\n"
                        f"⚡ Бесплатно • {users_db[user_id]['count']+1}/5",
                parse_mode='Markdown'
            )
        
        # Увеличиваем счетчик
        generator.increment_usage(user_id)
        
        # Удаляем статус
        bot.delete_message(message.chat.id, status_msg.message_id)
        
        # Удаляем файл
        os.remove(video_path)
    else:
        # Если ошибка, создаем демо
        video_path = generator.generate_demo_video(full_prompt, user_id)
        
        with open(video_path, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=f"✅ **Видео готово!** (демо-режим)\n\n"
                        f"*Запрос:* {prompt}\n"
                        f"*Стиль:* {style}\n\n"
                        f"⚡ Бесплатно • {users_db[user_id]['count']+1}/5",
                parse_mode='Markdown'
            )
        
        generator.increment_usage(user_id)
        bot.delete_message(message.chat.id, status_msg.message_id)
        os.remove(video_path)

@bot.message_handler(commands=['limits'])
@bot.message_handler(func=lambda m: m.text == "📊 Мои лимиты")
def show_limits(message):
    user_id = message.from_user.id
    generator.check_limits(user_id)  # Обновляем данные
    
    used = users_db.get(user_id, {}).get('count', 0)
    total = users_db.get(user_id, {}).get('total', 0)
    
    reset_time = datetime.now() + timedelta(days=1)
    
    # Создаем визуальный прогресс-бар
    progress = "█" * used + "░" * (5 - used)
    
    bot.send_message(
        message.chat.id,
        f"📊 **Ваши лимиты:**\n\n"
        f"`{progress}` {used}/5 на сегодня\n\n"
        f"📈 Всего создано видео: {total}\n"
        f"🔄 Сброс лимитов: {reset_time.strftime('%H:%M')}\n\n"
        f"✨ **Всегда бесплатно!**",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_message(message):
    help_text = """
❓ **Помощь и советы**

📝 **Как получить хорошее видео:**
• Опиши движение (бежит, летит, плывет)
• Укажи окружение (в космосе, в лесу)
• Добавь детали (цвета, освещение)
• Опиши настроение (веселое, мрачное)

🎨 **Стили:**
• Обычный - реалистичное видео
• Аниме - японская анимация
• 3D - компьютерная графика

⚠️ **Ограничения:**
• 5 видео в день (бесплатно)
• Длительность 2-3 секунды
• Качество 512x512

🌟 **Совет:** Чем подробнее описание, 
тем интереснее получится видео!

🆓 **Полностью бесплатно!**
    """
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['examples'])
def examples(message):
    examples = [
        "Космонавт играет в футбол на Марсе",
        "Розовый слон летит над городом",
        "Динозавр катается на скейтборде",
        "Кот-ниндзя бежит по крышам Токио",
        "Робот готовит пиццу в ресторане"
    ]
    
    markup = types.InlineKeyboardMarkup()
    for ex in examples:
        markup.add(types.InlineKeyboardButton(
            f"🎬 {ex[:30]}...",
            callback_data=f"ex_{ex}"
        ))
    
    bot.send_message(
        message.chat.id,
        "🎯 **Выберите пример:**",
        reply_markup=markup
    )

if __name__ == "__main__":
    print("🤖 Бесплатный бот запущен!")
    print("📱 Проверьте @BotFather для токена")
    print("⚡ Ожидание сообщений...")
    
    # Создаем папки
    os.makedirs("videos", exist_ok=True)
    
    # Запускаем бота
    bot.infinity_polling()
