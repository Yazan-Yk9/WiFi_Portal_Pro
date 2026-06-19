#!/bin/sh

# -----------------------------------------------------------------
# 🎯 English & Arabic Aliases for Live Container Management
# اختصارات ذكية باللغتين العربية والإنجليزية لإدارة وصيانة الشبكة حياً
# -----------------------------------------------------------------

# 1. Connected Devices List / استعراض الأجهزة المتصلة والأيبيهات
alias wifi-users="cat /var/lib/misc/dnsmasq.leases"

# 2. Reload Python Voucher System / تحديث وتطبيق أكواد المستخدمين حياً
alias wifi-reload-codes="pkill -f app.py && echo '✅ [EN] Vouchers updated live!' && echo '✅ [AR] تم تحديث الأكواد والرموز الزمنية حياً!'"

# 3. Apply Blocklist Domain Restrictions / تطبيق حظر المواقع والتطبيقات فوراً
alias wifi-reload-blocks="awk '{print \"address=/\"\$1\"/0.0.0.0/\"}' /etc/blocklist.txt > /etc/dnsmasq.adblock.conf && pkill -HUP dnsmasq && echo '✅ [EN] Blocklist updated live!' && echo '✅ [AR] تم تطبيق قائمة حظر المواقع حياً!'"

# 4. Show System Help / عرض هذه اللوحة التوجيهية في أي وقت
alias wifi-help="sh /etc/profile.d/aliases.sh"


# -----------------------------------------------------------------
# 📊 Visual Bilingual Welcome Dashboard / لوحة الترحيب التفاعلية المشتركة
# -----------------------------------------------------------------
clear
echo "=================================================================="
echo "🎯 WELCOME TO WI-FI AP PORTAL PRO / أهلاً بك في نظام إدارة الواي فاي"
echo "=================================================================="
echo ""
echo " 🇺🇸 [ENGLISH MANAGEMENT COMMANDS]:"
echo " 1. View connected devices & IPs     -> type: wifi-users"
echo " 2. Reload voucher system live       -> type: wifi-reload-codes"
echo " 3. Apply blocked domains instantly  -> type: wifi-reload-blocks"
echo " 4. Show this help dashboard again   -> type: wifi-help"
echo ""
echo " ----------------------------------------------------------------"
echo ""
echo " 	🇦🇪 [أوامر الإدارة والصيانة باللغة العربية]:"
echo " 1. لمعرفة الأجهزة المتصلة والأيبيهات  -> اكتب: wifi-users"
echo " 2. لتحديث أكواد المستخدمين حياً      -> اكتب: wifi-reload-codes"
echo " 3. لتطبيق قائمة حظر المواقع فوراً    -> اكتب: wifi-reload-blocks"
echo " 4. لعرض لوحة التحكم المساعدة هذه مجدداً -> اكتب: wifi-help"
echo ""
echo "=================================================================="
