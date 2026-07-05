# =============================================================================
# i18n.py — Système multilingue de Yorbity
# 6 langues : français, anglais, espagnol, portugais, chinois, arabe
# Détection auto de la langue selon le pays du visiteur (IP → pays → langue)
# + sélecteur manuel. À importer dans ui.py.
# =============================================================================
import urllib.request, json

# Langue par défaut selon le pays d'où se connecte le visiteur
PAYS_LANGUE = {
    # Francophones
    "FR":"fr","GA":"fr","CM":"fr","SN":"fr","CI":"fr","CD":"fr","CG":"fr","BJ":"fr",
    "TG":"fr","NE":"fr","BF":"fr","ML":"fr","GN":"fr","MG":"fr","RW":"fr","BI":"fr",
    "TD":"fr","CF":"fr","HT":"fr","DZ":"fr","MA":"fr","TN":"fr","MR":"fr","KM":"fr",
    "DJ":"fr","BE":"fr","CH":"fr","LU":"fr","MC":"fr","VU":"fr","SC":"fr",
    # Anglophones
    "US":"en","GB":"en","NG":"en","GH":"en","KE":"en","UG":"en","TZ":"en","ZA":"en",
    "ZM":"en","ZW":"en","MW":"en","SL":"en","LR":"en","GM":"en","BW":"en","NA":"en",
    "IN":"en","PK":"en","BD":"en","LK":"en","NP":"en","PH":"en","MY":"en","SG":"en",
    "AU":"en","NZ":"en","CA":"en","IE":"en","JM":"en","TT":"en","BB":"en","GY":"en",
    # Hispanophones
    "ES":"es","MX":"es","CO":"es","AR":"es","PE":"es","VE":"es","CL":"es","EC":"es",
    "GT":"es","CU":"es","BO":"es","DO":"es","HN":"es","PY":"es","NI":"es","CR":"es",
    "PA":"es","UY":"es","SV":"es","GQ":"es",
    # Lusophones
    "BR":"pt","PT":"pt","AO":"pt","MZ":"pt","CV":"pt","GW":"pt","ST":"pt","TL":"pt",
    # Sinophones
    "CN":"zh","TW":"zh","HK":"zh","MO":"zh",
    # Arabophones
    "EG":"ar","SA":"ar","AE":"ar","QA":"ar","KW":"ar","BH":"ar","OM":"ar","JO":"ar",
    "LB":"ar","IQ":"ar","SY":"ar","YE":"ar","LY":"ar","SD":"ar","PS":"ar",
}

LANGUES = {
    "fr":"🇫🇷 Français", "en":"🇬🇧 English", "es":"🇪🇸 Español",
    "pt":"🇧🇷 Português", "zh":"🇨🇳 中文", "ar":"🇸🇦 العربية",
}

RTL = {"ar"}  # langues écrites de droite à gauche

# ----------------------------------------------------------------------------
# Détection du pays du visiteur via son IP (service gratuit, sans clé)
# ----------------------------------------------------------------------------
def detecter_langue(defaut="fr"):
    try:
        req = urllib.request.Request("https://ipapi.co/json/",
                                     headers={"User-Agent":"Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=3).read())
        pays = data.get("country_code", "")
        return PAYS_LANGUE.get(pays, defaut)
    except Exception:
        return defaut

# ----------------------------------------------------------------------------
# Table de traduction de l'interface (libellés, boutons, titres)
# ----------------------------------------------------------------------------
T = {
 "tagline": {
   "fr":"Ta trajectoire vers le monde", "en":"Your trajectory to the world",
   "es":"Tu trayectoria hacia el mundo", "pt":"Sua trajetória para o mundo",
   "zh":"你通向世界的轨道", "ar":"مسارك نحو العالم"},
 "q_origine": {
   "fr":"🌍 Ton pays d'origine", "en":"🌍 Your home country",
   "es":"🌍 Tu país de origen", "pt":"🌍 Seu país de origem",
   "zh":"🌍 你的原籍国", "ar":"🌍 بلدك الأصلي"},
 "q_dest": {
   "fr":"🎯 Pays de destination", "en":"🎯 Destination country",
   "es":"🎯 País de destino", "pt":"🎯 País de destino",
   "zh":"🎯 目标国家", "ar":"🎯 بلد الوجهة"},
 "q_type": {
   "fr":"📌 Type de projet", "en":"📌 Project type",
   "es":"📌 Tipo de proyecto", "pt":"📌 Tipo de projeto",
   "zh":"📌 项目类型", "ar":"📌 نوع المشروع"},
 "q_niveau": {
   "fr":"🎓 Niveau visé", "en":"🎓 Target level",
   "es":"🎓 Nivel deseado", "pt":"🎓 Nível pretendido",
   "zh":"🎓 目标学历", "ar":"🎓 المستوى المطلوب"},
 "q_domaine": {
   "fr":"📚 Domaine d'études", "en":"📚 Field of study",
   "es":"📚 Área de estudio", "pt":"📚 Área de estudo",
   "zh":"📚 学习领域", "ar":"📚 مجال الدراسة"},
 "choisir": {
   "fr":"Choisir…", "en":"Choose…", "es":"Elegir…", "pt":"Escolher…",
   "zh":"选择…", "ar":"اختر…"},
 "intro": {
   "fr":"👆 Réponds aux 4 questions : ton parcours détaillé s'affiche instantanément ici.",
   "en":"👆 Answer the 4 questions: your detailed path appears instantly here.",
   "es":"👆 Responde las 4 preguntas: tu recorrido detallado aparece al instante aquí.",
   "pt":"👆 Responda às 4 perguntas: seu percurso detalhado aparece aqui na hora.",
   "zh":"👆 回答这4个问题，你的详细路径将立即显示在这里。",
   "ar":"👆 أجب عن الأسئلة الأربعة: سيظهر مسارك المفصل هنا فورًا."},
 "start_from": {
   "fr":"✨ Commence ton projet à partir de", "en":"✨ Start your project from",
   "es":"✨ Comienza tu proyecto desde", "pt":"✨ Comece seu projeto a partir de",
   "zh":"✨ 开启你的项目，仅需", "ar":"✨ ابدأ مشروعك بدءًا من"},
 "budget": {
   "fr":"💶 Budget à prouver :", "en":"💶 Funds to prove:",
   "es":"💶 Fondos a justificar:", "pt":"💶 Fundos a comprovar:",
   "zh":"💶 需证明的资金：", "ar":"💶 المبلغ المطلوب إثباته:"},
 "travail": {
   "fr":"⚖️ Travail étudiant :", "en":"⚖️ Student work:",
   "es":"⚖️ Trabajo estudiantil:", "pt":"⚖️ Trabalho estudantil:",
   "zh":"⚖️ 学生工作：", "ar":"⚖️ عمل الطلاب:"},
 "apres": {
   "fr":"🎯 Après le diplôme :", "en":"🎯 After graduation:",
   "es":"🎯 Después del diploma:", "pt":"🎯 Após o diploma:",
   "zh":"🎯 毕业后：", "ar":"🎯 بعد التخرج:"},
 "chemin": {
   "fr":"🗺️ Ton chemin, étape par étape", "en":"🗺️ Your path, step by step",
   "es":"🗺️ Tu camino, paso a paso", "pt":"🗺️ Seu caminho, passo a passo",
   "zh":"🗺️ 你的路径，逐步指引", "ar":"🗺️ طريقك، خطوة بخطوة"},
 "etape": {
   "fr":"Étape", "en":"Step", "es":"Paso", "pt":"Etapa", "zh":"步骤", "ar":"خطوة"},
 "lien_officiel": {
   "fr":"🔗 Lien officiel", "en":"🔗 Official link", "es":"🔗 Enlace oficial",
   "pt":"🔗 Link oficial", "zh":"🔗 官方链接", "ar":"🔗 الرابط الرسمي"},
 "aide_etape": {
   "fr":"🤝 Besoin d'aide pour cette étape ? On s'en occupe",
   "en":"🤝 Need help with this step? We handle it",
   "es":"🤝 ¿Necesitas ayuda con este paso? Nos encargamos",
   "pt":"🤝 Precisa de ajuda nesta etapa? Cuidamos disso",
   "zh":"🤝 这一步需要帮助吗？我们来处理",
   "ar":"🤝 هل تحتاج مساعدة في هذه الخطوة؟ نحن نتكفل بذلك"},
 "portail": {
   "fr":"🌐 Portail officiel —", "en":"🌐 Official portal —",
   "es":"🌐 Portal oficial —", "pt":"🌐 Portal oficial —",
   "zh":"🌐 官方门户 —", "ar":"🌐 البوابة الرسمية —"},
 "bourses_pour_toi": {
   "fr":"💰 Les bourses pour toi", "en":"💰 Scholarships for you",
   "es":"💰 Becas para ti", "pt":"💰 Bolsas para você",
   "zh":"💰 适合你的奖学金", "ar":"💰 المنح الدراسية لك"},
 "accompagne": {
   "fr":"🤝 On t'accompagne jusqu'en", "en":"🤝 We support you all the way to",
   "es":"🤝 Te acompañamos hasta", "pt":"🤝 Acompanhamos você até",
   "zh":"🤝 我们全程陪伴你前往", "ar":"🤝 نرافقك حتى"},
 "accompagne_desc": {
   "fr":"Choisis les démarches que tu veux déléguer — notre équipe s'en charge, tu gardes le contrôle à chaque étape.",
   "en":"Choose the steps you want to delegate — our team handles them, you stay in control at every stage.",
   "es":"Elige los trámites que quieras delegar — nuestro equipo se encarga, tú mantienes el control en cada etapa.",
   "pt":"Escolha as etapas que deseja delegar — nossa equipe cuida de tudo, você mantém o controle em cada fase.",
   "zh":"选择你想委托的步骤——我们的团队负责处理，你在每个阶段都掌握主动权。",
   "ar":"اختر الإجراءات التي تريد تفويضها — يتولى فريقنا الأمر، وتبقى أنت المتحكم في كل مرحلة."},
 "form_titre": {
   "fr":"📩 Parle-nous de ton projet — réponse sous 24 h",
   "en":"📩 Tell us about your project — reply within 24h",
   "es":"📩 Cuéntanos tu proyecto — respuesta en 24h",
   "pt":"📩 Fale sobre seu projeto — resposta em 24h",
   "zh":"📩 告诉我们你的项目——24小时内回复",
   "ar":"📩 أخبرنا عن مشروعك — الرد خلال 24 ساعة"},
 "nom": {
   "fr":"Ton nom complet", "en":"Your full name", "es":"Tu nombre completo",
   "pt":"Seu nome completo", "zh":"你的全名", "ar":"اسمك الكامل"},
 "contact": {
   "fr":"WhatsApp ou e-mail", "en":"WhatsApp or e-mail", "es":"WhatsApp o correo",
   "pt":"WhatsApp ou e-mail", "zh":"WhatsApp 或电子邮箱", "ar":"واتساب أو البريد الإلكتروني"},
 "service_interet": {
   "fr":"La démarche qui t'intéresse", "en":"The service you're interested in",
   "es":"El servicio que te interesa", "pt":"O serviço que te interessa",
   "zh":"你感兴趣的服务", "ar":"الخدمة التي تهمك"},
 "projet_2lignes": {
   "fr":"Ton projet en 2 lignes (optionnel)", "en":"Your project in 2 lines (optional)",
   "es":"Tu proyecto en 2 líneas (opcional)", "pt":"Seu projeto em 2 linhas (opcional)",
   "zh":"用两行描述你的项目（可选）", "ar":"مشروعك في سطرين (اختياري)"},
 "lancer": {
   "fr":"🚀 Lancer mon projet", "en":"🚀 Launch my project",
   "es":"🚀 Iniciar mi proyecto", "pt":"🚀 Lançar meu projeto",
   "zh":"🚀 启动我的项目", "ar":"🚀 ابدأ مشروعي"},
 "recu": {
   "fr":"✅ Reçu ! Un conseiller te contacte sous 24–48 h avec un devis personnalisé.",
   "en":"✅ Received! An advisor will contact you within 24–48h with a personalized quote.",
   "es":"✅ ¡Recibido! Un asesor te contactará en 24–48h con un presupuesto personalizado.",
   "pt":"✅ Recebido! Um consultor entrará em contato em 24–48h com um orçamento personalizado.",
   "zh":"✅ 已收到！顾问将在24–48小时内联系你并提供个性化报价。",
   "ar":"✅ تم الاستلام! سيتواصل معك مستشار خلال 24–48 ساعة مع عرض سعر مخصص."},
 "champs_requis": {
   "fr":"Nom et contact sont obligatoires.", "en":"Name and contact are required.",
   "es":"Nombre y contacto son obligatorios.", "pt":"Nome e contato são obrigatórios.",
   "zh":"姓名和联系方式为必填项。", "ar":"الاسم ووسيلة التواصل مطلوبان."},
 "disclaimer": {
   "fr":"Nous préparons et organisons tes démarches avec toi. Personne ne peut garantir une admission ou un visa — méfie-toi de ceux qui le promettent.",
   "en":"We prepare and organize your steps with you. No one can guarantee an admission or a visa — beware of those who promise it.",
   "es":"Preparamos y organizamos tus trámites contigo. Nadie puede garantizar una admisión o una visa — desconfía de quienes lo prometen.",
   "pt":"Preparamos e organizamos suas etapas com você. Ninguém pode garantir uma admissão ou visto — desconfie de quem promete.",
   "zh":"我们与你一起准备和组织各项手续。没有人能保证录取或签证——请警惕那些做出此类承诺的人。",
   "ar":"نحن نُعدّ وننظّم إجراءاتك معك. لا أحد يستطيع ضمان القبول أو التأشيرة — احذر ممن يعدك بذلك."},
 "langue_label": {
   "fr":"Langue", "en":"Language", "es":"Idioma", "pt":"Idioma", "zh":"语言", "ar":"اللغة"},
 "types": {
   "fr":["Formation (admission)","Bourse","Stage / Emploi étudiant"],
   "en":["Program (admission)","Scholarship","Internship / Student job"],
   "es":["Formación (admisión)","Beca","Prácticas / Empleo estudiantil"],
   "pt":["Formação (admissão)","Bolsa","Estágio / Emprego estudantil"],
   "zh":["课程（录取）","奖学金","实习 / 学生工作"],
   "ar":["برنامج (قبول)","منحة دراسية","تدريب / عمل طلابي"]},
 "niveaux": {
   "fr":["Licence / Bachelor","Master","Doctorat","Formation professionnelle","Je suis au lycée"],
   "en":["Bachelor","Master","PhD","Vocational training","I'm in high school"],
   "es":["Licenciatura","Máster","Doctorado","Formación profesional","Estoy en secundaria"],
   "pt":["Licenciatura","Mestrado","Doutorado","Formação profissional","Estou no ensino médio"],
   "zh":["本科","硕士","博士","职业培训","我在读高中"],
   "ar":["بكالوريوس","ماجستير","دكتوراه","تدريب مهني","أنا في الثانوية"]},
 "domaines": {
   "fr":["Tous les domaines","Informatique & numérique","Ingénierie","Santé & médecine","Gestion, commerce & finance","Droit & sciences politiques","Sciences","Agriculture & environnement","Arts, design & architecture","Lettres & sciences humaines","Éducation","Tourisme & hôtellerie"],
   "en":["All fields","IT & digital","Engineering","Health & medicine","Business, trade & finance","Law & political science","Sciences","Agriculture & environment","Arts, design & architecture","Humanities","Education","Tourism & hospitality"],
   "es":["Todas las áreas","Informática y digital","Ingeniería","Salud y medicina","Gestión, comercio y finanzas","Derecho y ciencias políticas","Ciencias","Agricultura y medio ambiente","Artes, diseño y arquitectura","Humanidades","Educación","Turismo y hostelería"],
   "pt":["Todas as áreas","Informática e digital","Engenharia","Saúde e medicina","Gestão, comércio e finanças","Direito e ciências políticas","Ciências","Agricultura e ambiente","Artes, design e arquitetura","Humanidades","Educação","Turismo e hotelaria"],
   "zh":["所有领域","信息技术与数字","工程","健康与医学","管理、商业与金融","法律与政治学","理学","农业与环境","艺术、设计与建筑","人文学科","教育","旅游与酒店管理"],
   "ar":["جميع المجالات","تقنية المعلومات والرقمية","الهندسة","الصحة والطب","الإدارة والتجارة والمالية","القانون والعلوم السياسية","العلوم","الزراعة والبيئة","الفنون والتصميم والعمارة","العلوم الإنسانية","التعليم","السياحة والضيافة"]},
}

def t(cle, lang):
    """Retourne la traduction d'une clé, avec repli sur le français."""
    v = T.get(cle, {})
    return v.get(lang, v.get("fr", cle))
