import json
import os

class Localization:
    def __init__(self, bot):
        self.bot = bot
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load translation files"""
        locales_dir = os.path.join(self.bot.base_path, 'locales')
        if not os.path.exists(locales_dir):
            os.makedirs(locales_dir)
            # Create default English translations
            self.create_default_translations(locales_dir)
        
        # Load all translation files
        for filename in os.listdir(locales_dir):
            if filename.endswith('.json'):
                locale = filename[:-5]  # Remove .json extension
                with open(os.path.join(locales_dir, filename), 'r', encoding='utf-8') as f:
                    self.translations[locale] = json.load(f)
    
    def create_default_translations(self, locales_dir):
        """Create default English translations"""
        en_translations = {
            "dashboard_title": "🤖 AI Discord Bot Dashboard",
            "dashboard_description": "Welcome to the comprehensive bot control panel",
            "control_panel": "🎛️ Control Panel",
            "control_panel_desc": "Use the buttons below to navigate through different sections",
            "statistics": "📊 Statistics",
            "statistics_desc": "View detailed analytics and usage metrics",
            "settings": "⚙️ Settings",
            "settings_desc": "Configure bot preferences and behavior",
            "models": "📋 Models",
            "models_desc": "Manage AI models and configurations",
            "bot_status": "📊 Bot Status",
            "bot_status_desc": "Current bot status and performance metrics",
            "users": "👥 Users",
            "servers": "🖥️ Servers",
            "uptime": "⏰ Uptime",
            "latency": "⚡ Latency",
            "version": "💾 Version",
            "bot_statistics": "📈 Bot Statistics",
            "bot_statistics_desc": "Comprehensive statistics and analytics",
            "total_users": "👥 Total Users",
            "total_conversations": "💬 Total Conversations",
            "code_generations": "💻 Code Generations",
            "recent_activity": "📅 Recent Activity (24h)",
            "bot_settings": "⚙️ Bot Settings",
            "bot_settings_desc": "Configure bot preferences",
            "prefix": "🔤 Prefix",
            "default_model": "🤖 Default Model",
            "change_prefix": "🔤 Change Prefix",
            "set_default_model": "🤖 Set Default Model",
            "available_models": "📋 Available Models",
            "manage_models": "Manage AI models",
            "add_model": "➕ Add Model",
            "remove_model": "🗑️ Remove Model",
            "new_prefix": "New Prefix",
            "enter_new_prefix": "Enter new prefix...",
            "prefix_updated": "✅ Prefix Updated",
            "new_prefix_value": "New prefix: `{prefix}`",
            "default_model_set": "✅ Default Model Set",
            "new_default_model": "New default model: **{model}**",
            "error_updating_prefix": "❌ Error updating prefix: {error}",
            "error_setting_default": "❌ Error setting default model: {error}",
            "no_models_available": "❌ No models available.",
            "model_not_found": "❌ Model not found.",
            "model_manager_unavailable": "❌ Model manager not available."
        }
        
        with open(os.path.join(locales_dir, 'en.json'), 'w', encoding='utf-8') as f:
            json.dump(en_translations, f, indent=4, ensure_ascii=False)
        
        # Create Arabic translations
        ar_translations = {
            "dashboard_title": "🤖 لوحة تحكم بوت الـ Discord AI",
            "dashboard_description": "مرحبًا بك في لوحة التحكم الشاملة للبوت",
            "control_panel": "🎛️ لوحة التحكم",
            "control_panel_desc": "استخدم الأزرار أدناه للتنقل بين الأقسام المختلفة",
            "statistics": "📊 الإحصائيات",
            "statistics_desc": "عرض التحليلات والإحصائيات المفصلة",
            "settings": "⚙️ الإعدادات",
            "settings_desc": "تكوين تفضيلات البوت والسلوك",
            "models": "📋 النماذج",
            "models_desc": "إدارة نماذج الذكاء الاصطناعي والتكوينات",
            "bot_status": "📊 حالة البوت",
            "bot_status_desc": "حالة البوت وأداءه الحالي",
            "users": "👥 المستخدمون",
            "servers": "🖥️ الخوادم",
            "uptime": "⏰ وقت التشغيل",
            "latency": "⚡ زمن الاستجابة",
            "version": "💾 الإصدار",
            "bot_statistics": "📈 إحصائيات البوت",
            "bot_statistics_desc": "إحصائيات وتحليلات شاملة",
            "total_users": "👥 إجمالي المستخدمين",
            "total_conversations": "💬 إجمالي المحادثات",
            "code_generations": "💻 توليدات الكود",
            "recent_activity": "📅 النشاط الأخير (24 ساعة)",
            "bot_settings": "⚙️ إعدادات البوت",
            "bot_settings_desc": "تكوين تفضيلات البوت",
            "prefix": "🔤 البادئة",
            "default_model": "🤖 النموذج الافتراضي",
            "change_prefix": "🔤 تغيير البادئة",
            "set_default_model": "🤖 تعيين النموذج الافتراضي",
            "available_models": "📋 النماذج المتاحة",
            "manage_models": "إدارة نماذج الذكاء الاصطناعي",
            "add_model": "➕ إضافة نموذج",
            "remove_model": "🗑️ إزالة نموذج",
            "new_prefix": "بادئة جديدة",
            "enter_new_prefix": "أدخل البادئة الجديدة...",
            "prefix_updated": "✅ تم تحديث البادئة",
            "new_prefix_value": "البادئة الجديدة: `{prefix}`",
            "default_model_set": "✅ تم تعيين النموذج الافتراضي",
            "new_default_model": "النموذج الافتراضي الجديد: **{model}**",
            "error_updating_prefix": "❌ خطأ في تحديث البادئة: {error}",
            "error_setting_default": "❌ خطأ في تعيين النموذج الافتراضي: {error}",
            "no_models_available": "❌ لا توجد نماذج متاحة.",
            "model_not_found": "❌ النموذج غير موجود.",
            "model_manager_unavailable": "❌ مدير النماذج غير متاح."
        }
        
        with open(os.path.join(locales_dir, 'ar.json'), 'w', encoding='utf-8') as f:
            json.dump(ar_translations, f, indent=4, ensure_ascii=False)
    
    def get_text(self, key, locale='en', **kwargs):
        """Get translated text"""
        if locale in self.translations and key in self.translations[locale]:
            text = self.translations[locale][key]
            # Replace placeholders
            for placeholder, value in kwargs.items():
                text = text.replace(f'{{{placeholder}}}', str(value))
            return text
        # Fallback to English
        elif 'en' in self.translations and key in self.translations['en']:
            text = self.translations['en'][key]
            # Replace placeholders
            for placeholder, value in kwargs.items():
                text = text.replace(f'{{{placeholder}}}', str(value))
            return text
        # Fallback to key
        return key
    
    def get_user_locale(self, user_id):
        """Get user's preferred locale (simplified implementation)"""
        # In a real implementation, this would check user preferences
        # For now, we'll default to English
        return 'en'