import json
import os

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Only initialize OpenAI if API key is available
openai = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        pass

def chat_with_sahilkamp_bot(user_message):
    """SahilKamp AI chatbot with smart responses"""
    
    # If no OpenAI available, return smart fallback response
    if not openai or not OPENAI_API_KEY:
        return get_fallback_response(user_message)
    
    try:
        system_prompt = """Sen SahilKamp İstanbul'un AI asistanısın. Çok akıllı, yardımsever ve dostane bir asistansın.
        
        SahilKamp Bilgileri:
        - Hafta sonu çadır kamp: 750 TL kişi başı (kahvaltı, akşam yemeği ve aktiviteler dahil)
        - Hafta içi çadır kamp: 550 TL kişi başı
        - Çadır kiralama: 150 TL/gece
        - Aktiviteler: Kano, trekking, ateş başı etkinlikleri, doğa yürüyüşü
        - Pet-friendly alanlar mevcut (50 TL ek ücret)
        - Çocuk aktivite alanları var
        - Ulaşım: İstanbul'dan otobüs seferleri (Pazartesi-Cumartesi)
        - Rezervasyon: %30 ön ödeme, kalan check-in'de
        - Özel diyet ihtiyaçları karşılanır
        - Check-in: 15:00, Check-out: 12:00
        
        Kısa, dostane ve bilgilendirici cevaplar ver. Emoji kullan."""

        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return get_fallback_response(user_message)

def get_fallback_response(user_message):
    """Smart fallback responses when OpenAI is not available"""
    message = user_message.lower()
    
    # SahilKamp specific responses
    if any(keyword in message for keyword in ['fiyat', 'ücret', 'para', 'kaç tl', 'ne kadar']):
        return "🏕️ SahilKamp fiyatlarımız:\n• Hafta sonu: 750 TL/kişi\n• Hafta içi: 550 TL/kişi\n• Çadır kiralama: 150 TL/gece\nKahvaltı, akşam yemeği ve aktiviteler dahil! ✨"
    
    elif any(keyword in message for keyword in ['aktivite', 'etkinlik', 'yapabilir', 'neler var']):
        return "🚣‍♀️ SahilKamp aktivitelerimiz:\n• Kano turları\n• Doğa yürüyüşleri\n• Ateş başı etkinlikleri\n• Trekking rotaları\nHepsine katılım ücretsiz! 🏃‍♂️"
    
    elif any(keyword in message for keyword in ['rezervasyon', 'ayırt', 'yer', 'rezerve']):
        return "📅 Rezervasyon için:\n• %30 ön ödeme yeterli\n• Check-in: 15:00\n• Check-out: 12:00\n• Kalan ödeme check-in sırasında\nHemen yer ayırtalım! 🎪"
    
    elif any(keyword in message for keyword in ['pet', 'hayvan', 'köpek', 'kedi', 'evcil']):
        return "🐕 Pet-friendly alanlarımız var!\n• 50 TL ek ücret\n• Özel pet alanları\n• Su ve mama kabı sağlanır\nTüylü dostlarınızla gelin! 🐾"
    
    elif any(keyword in message for keyword in ['ulaşım', 'nasıl gelir', 'yol', 'otobüs']):
        return "🚌 Ulaşım seçenekleri:\n• İstanbul'dan düzenli otobüs seferleri\n• Pazartesi-Cumartesi günleri\n• Kendi aracınızla da gelebilirsiniz\nDetaylı yol tarifi gönderebilirim! 🗺️"
        
    elif any(keyword in message for keyword in ['çadır', 'kamp', 'equipment']):
        return "⛺ Çadır ve ekipman:\n• Kendi çadırınızı getirebilirsiniz\n• Bizden de kiralayabilirsiniz (150 TL/gece)\n• Uyku tulumu ve matras dahil\nTercihinizi belirtin! 🎒"
    
    elif 'merhaba' in message or 'selam' in message or 'hello' in message:
        return "Merhaba! 👋 SahilKamp İstanbul'a hoşgeldiniz! \nSize nasıl yardımcı olabilirim? Fiyatlar, aktiviteler, rezervasyon... Her konuda yanınızdayım! 🏕️✨"
    
    else:
        return "🤖 Size yardımcı olmaya çalışıyorum! SahilKamp hakkında:\n• Fiyatlar ve paketler\n• Aktiviteler ve etkinlikler\n• Rezervasyon bilgileri\n• Pet policy\nHangi konuda bilgi almak istersiniz? 🌟"