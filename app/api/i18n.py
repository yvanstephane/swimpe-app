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
 "it": "🇮🇹 Italiano",
 "de": "Deutsch",
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
  "nom_legal_note": {
   "fr":"Tel qu'il apparaîtra sur tes dossiers officiels.",
   "en":"As it will appear on your official files.",
   "es":"Tal como aparecerá en tus expedientes oficiales.",
   "pt":"Como aparecerá nos seus dossiês oficiais.",
   "zh":"将显示在你的正式档案中的姓名。",
   "ar":"كما سيظهر في ملفاتك الرسمية.",
   "ja":"正式な書類に記載される氏名です。",
   "ko":"공식 서류에 표시될 이름입니다.",
   "id":"Seperti yang akan tercantum pada berkas resmimu."},
 "tagline": {
   "fr":"Ta trajectoire vers le monde", "en":"Your trajectory to the world",
   "es":"Tu trayectoria hacia el mundo", "pt":"Sua trajetória para o mundo",
   "zh":"你通向世界的轨道", "ar":"مسارك نحو العالم"},
 "q_origine": {
   "fr":"🛂 Ta nationalité (passeport)", "en":"🛂 Your nationality (passport)",
   "es":"🛂 Tu nacionalidad (pasaporte)", "pt":"🛂 Sua nacionalidade (passaporte)",
   "zh":"🛂 你的国籍（护照）", "ar":"🛂 جنسيتك (جواز السفر)"},
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
  "questionnaire_btn": {
   "fr":"Trouve mon meilleur projet", "en":"Find my best-fit project",
   "es":"Encuentra mi mejor proyecto", "pt":"Encontra o meu melhor projeto",
   "zh":"找到最适合我的项目", "ar":"ابحث عن أفضل مشروع لي",
   "ja":"最適なプロジェクトを見つける", "ko":"나에게 맞는 프로젝트 찾기",
   "id":"Temukan proyek terbaik saya"},

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
   "fr":"🤝 On t'accompagne dans ton projet —", "en":"🤝 We guide you through your project —",
   "es":"🤝 Te acompañamos en tu proyecto —", "pt":"🤝 Acompanhamos você no seu projeto —",
   "de":"🤝 Wir begleiten dich bei deinem Projekt —",
   "zh":"🤝 我们陪你推进你的项目 —", "ar":"🤝 نرافقك في مشروعك —"},
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
   "fr":["Formation (admission)","Bourse","Stage / Emploi étudiant","Métier spécialisé","Sport","Art","Volontariat"],
   "en":["Program (admission)","Scholarship","Internship / Student job","Skilled trade","Sports","Arts","Volunteering"],
   "es":["Formación (admisión)","Beca","Prácticas / Empleo estudiantil","Oficio especializado","Deporte","Arte","Voluntariado"],
   "pt":["Formação (admissão)","Bolsa","Estágio / Emprego estudantil","Ofício especializado","Esporte","Arte","Voluntariado"],
   "zh":["课程（录取）","奖学金","实习 / 学生工作","技术工种","体育","艺术","志愿服务"],
   "ar":["برنامج (قبول)","منحة دراسية","تدريب / عمل طلابي","مهنة متخصصة","الرياضة","الفنون","التطوع"]},
 "disciplines": {
  "Volontariat": {
   "fr":["Éducation","Santé","Environnement","Humanitaire & social","Culture","Droits humains","Numérique","Agriculture","Autre domaine"],
   "en":["Education","Health","Environment","Humanitarian & social","Culture","Human rights","Digital","Agriculture","Other field"],
   "es":["Educación","Salud","Medio ambiente","Humanitario y social","Cultura","Derechos humanos","Digital","Agricultura","Otro ámbito"],
   "pt":["Educação","Saúde","Meio ambiente","Humanitário e social","Cultura","Direitos humanos","Digital","Agricultura","Outro domínio"],
   "zh":["教育","健康","环境","人道与社会","文化","人权","数字技术","农业","其他领域"],
   "ar":["التعليم","الصحة","البيئة","العمل الإنساني والاجتماعي","الثقافة","حقوق الإنسان","الرقمنة","الزراعة","مجال آخر"]},
  "Sport": {
   "fr":["Football","Basketball","Athlétisme","Natation","Tennis","Rugby","Volleyball","Cyclisme","Arts martiaux","Autre discipline"],
   "en":["Football (Soccer)","Basketball","Athletics","Swimming","Tennis","Rugby","Volleyball","Cycling","Martial arts","Other discipline"],
   "es":["Fútbol","Baloncesto","Atletismo","Natación","Tenis","Rugby","Voleibol","Ciclismo","Artes marciales","Otra disciplina"],
   "pt":["Futebol","Basquete","Atletismo","Natação","Tênis","Rugby","Vôlei","Ciclismo","Artes marciais","Outra disciplina"],
   "zh":["足球","篮球","田径","游泳","网球","橄榄球","排球","自行车","武术","其他项目"],
   "ar":["كرة القدم","كرة السلة","ألعاب القوى","السباحة","التنس","الرغبي","الكرة الطائرة","ركوب الدراجات","الفنون القتالية","تخصص آخر"]},
  "Art": {
   "fr":["Musique","Danse","Arts visuels","Théâtre","Cinéma & audiovisuel","Design","Photographie","Écriture & littérature","Autre discipline"],
   "en":["Music","Dance","Visual arts","Theatre","Film & audiovisual","Design","Photography","Writing & literature","Other discipline"],
   "es":["Música","Danza","Artes visuales","Teatro","Cine y audiovisual","Diseño","Fotografía","Escritura y literatura","Otra disciplina"],
   "pt":["Música","Dança","Artes visuais","Teatro","Cinema e audiovisual","Design","Fotografia","Escrita e literatura","Outra disciplina"],
   "zh":["音乐","舞蹈","视觉艺术","戏剧","电影与影视","设计","摄影","写作与文学","其他项目"],
   "ar":["الموسيقى","الرقص","الفنون البصرية","المسرح","السينما والوسائط السمعية البصرية","التصميم","التصوير الفوتوغرافي","الكتابة والأدب","تخصص آخر"]}},
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


# --- Textes des comptes / connexion / premium (ajout) ---
T["compte_titre"] = {"fr":"👤 Mon compte","en":"👤 My account","es":"👤 Mi cuenta","pt":"👤 Minha conta","zh":"👤 我的账户","ar":"👤 حسابي","ja":"👤 マイアカウント","ko":"👤 내 계정","id":"👤 Akun saya"}
T["compte_invite"] = {"fr":"Connecte-toi pour débloquer les bourses détaillées et suivre tes projets.","en":"Sign in to unlock detailed scholarships and track your projects.","es":"Inicia sesión para desbloquear las becas detalladas y seguir tus proyectos.","pt":"Entre para desbloquear as bolsas detalhadas e acompanhar seus projetos.","zh":"登录以解锁详细奖学金并跟踪你的项目。","ar":"سجّل الدخول لفتح المنح التفصيلية ومتابعة مشاريعك.","ja":"ログインすると詳細な奨学金情報が見られ、プロジェクトを追跡できます。","ko":"로그인하면 상세 장학금 정보를 열람하고 프로젝트를 추적할 수 있습니다.","id":"Masuk untuk membuka beasiswa terperinci dan melacak proyekmu."}
T["btn_connexion"] = {"fr":"Se connecter / S'inscrire","en":"Sign in / Sign up","es":"Iniciar sesión / Registrarse","pt":"Entrar / Cadastrar","zh":"登录 / 注册","ar":"تسجيل الدخول / إنشاء حساب","ja":"ログイン / 新規登録","ko":"로그인 / 회원가입","id":"Masuk / Daftar"}
T["btn_deconnexion"] = {"fr":"Se déconnecter","en":"Sign out","es":"Cerrar sesión","pt":"Sair","zh":"退出登录","ar":"تسجيل الخروج","ja":"ログアウト","ko":"로그아웃","id":"Keluar"}
T["compte_gratuit"] = {"fr":"Compte gratuit","en":"Free account","es":"Cuenta gratuita","pt":"Conta gratuita","zh":"免费账户","ar":"حساب مجاني","ja":"無料アカウント","ko":"무료 계정","id":"Akun gratis"}
T["premium_actif"] = {"fr":"⭐ Premium actif","en":"⭐ Premium active","es":"⭐ Premium activo","pt":"⭐ Premium ativo","zh":"⭐ 高级会员已激活","ar":"⭐ العضوية المميزة مفعّلة","ja":"⭐ プレミアム有効","ko":"⭐ 프리미엄 활성","id":"⭐ Premium aktif"}
T["onglet_connexion"] = {"fr":"Se connecter","en":"Sign in","es":"Iniciar sesión","pt":"Entrar","zh":"登录","ar":"تسجيل الدخول","ja":"ログイン","ko":"로그인","id":"Masuk"}
T["onglet_inscription"] = {"fr":"Créer un compte","en":"Create account","es":"Crear cuenta","pt":"Criar conta","zh":"注册账户","ar":"إنشاء حساب","ja":"アカウント作成","ko":"계정 만들기","id":"Buat akun"}
T["bienvenue"] = {"fr":"👤 Bienvenue sur Yorbity","en":"👤 Welcome to Yorbity","es":"👤 Bienvenido a Yorbity","pt":"👤 Bem-vindo ao Yorbity","zh":"👤 欢迎来到 Yorbity","ar":"👤 مرحبًا بك في Yorbity","ja":"👤 Yorbity へようこそ","ko":"👤 Yorbity에 오신 것을 환영합니다","id":"👤 Selamat datang di Yorbity"}
T["champ_email"] = {"fr":"E-mail","en":"E-mail","es":"Correo","pt":"E-mail","zh":"电子邮箱","ar":"البريد الإلكتروني","ja":"メール","ko":"이메일","id":"E-mail"}
T["champ_pwd"] = {"fr":"Mot de passe","en":"Password","es":"Contraseña","pt":"Senha","zh":"密码","ar":"كلمة المرور","ja":"パスワード","ko":"비밀번호","id":"Kata sandi"}
T["champ_pwd2"] = {"fr":"Confirme le mot de passe","en":"Confirm password","es":"Confirma la contraseña","pt":"Confirme a senha","zh":"确认密码","ar":"أكّد كلمة المرور","ja":"パスワード確認","ko":"비밀번호 확인","id":"Konfirmasi kata sandi"}
T["champ_nom"] = {"fr":"Nom complet","en":"Full name","es":"Nombre completo","pt":"Nome completo","zh":"全名","ar":"الاسم الكامل","ja":"氏名","ko":"성명","id":"Nama lengkap"}
T["champ_pays"] = {"fr":"Nationalité","en":"Nationality","es":"Nacionalidad","pt":"Nacionalidade","zh":"国籍","ar":"الجنسية","ja":"国籍","ko":"국적","id":"Kewarganegaraan"}
T["champ_tel"] = {"fr":"Téléphone / WhatsApp (optionnel)","en":"Phone / WhatsApp (optional)","es":"Teléfono / WhatsApp (opcional)","pt":"Telefone / WhatsApp (opcional)","zh":"电话 / WhatsApp（可选）","ar":"الهاتف / واتساب (اختياري)","ja":"電話 / WhatsApp（任意）","ko":"전화 / WhatsApp (선택)","id":"Telepon / WhatsApp (opsional)"}
T["tel_note"] = {"fr":"Sert à récupérer ton compte par WhatsApp si tu perds ton mot de passe.","en":"Used to recover your account via WhatsApp if you lose your password.","es":"Sirve para recuperar tu cuenta por WhatsApp si pierdes tu contraseña.","pt":"Serve para recuperar sua conta pelo WhatsApp se perder a senha.","zh":"若忘记密码，可通过 WhatsApp 找回账户。","ar":"يُستخدم لاستعادة حسابك عبر واتساب إذا فقدت كلمة المرور.","ja":"パスワードを忘れた場合、WhatsApp でアカウントを復元するために使います。","ko":"비밀번호를 잊었을 때 WhatsApp으로 계정을 복구하는 데 사용됩니다.","id":"Digunakan untuk memulihkan akunmu lewat WhatsApp jika lupa kata sandi."}
T["btn_connecter"] = {"fr":"Se connecter","en":"Sign in","es":"Iniciar sesión","pt":"Entrar","zh":"登录","ar":"تسجيل الدخول","ja":"ログイン","ko":"로그인","id":"Masuk"}
T["btn_creer"] = {"fr":"Créer mon compte","en":"Create my account","es":"Crear mi cuenta","pt":"Criar minha conta","zh":"创建我的账户","ar":"إنشاء حسابي","ja":"アカウントを作成","ko":"계정 만들기","id":"Buat akun saya"}
T["btn_retour"] = {"fr":"Retour","en":"Back","es":"Volver","pt":"Voltar","zh":"返回","ar":"رجوع","ja":"戻る","ko":"뒤로","id":"Kembali"}
T["pwd_hint"] = {"fr":"Mot de passe (8 caractères min., 1 chiffre)","en":"Password (8 chars min., 1 digit)","es":"Contraseña (mín. 8 caracteres, 1 número)","pt":"Senha (mín. 8 caracteres, 1 número)","zh":"密码（至少8位，含1个数字）","ar":"كلمة المرور (8 أحرف على الأقل، رقم واحد)","ja":"パスワード（8文字以上、数字1つ）","ko":"비밀번호 (8자 이상, 숫자 1개)","id":"Kata sandi (min. 8 karakter, 1 angka)"}
T["pwd_diff"] = {"fr":"Les deux mots de passe ne correspondent pas.","en":"The two passwords do not match.","es":"Las dos contraseñas no coinciden.","pt":"As duas senhas não coincidem.","zh":"两次输入的密码不一致。","ar":"كلمتا المرور غير متطابقتين.","ja":"パスワードが一致しません。","ko":"두 비밀번호가 일치하지 않습니다.","id":"Kedua kata sandi tidak cocok."}
T["compte_cree"] = {"fr":"✅ Compte créé ! Bienvenue.","en":"✅ Account created! Welcome.","es":"✅ ¡Cuenta creada! Bienvenido.","pt":"✅ Conta criada! Bem-vindo.","zh":"✅ 账户已创建！欢迎。","ar":"✅ تم إنشاء الحساب! مرحبًا.","ja":"✅ アカウントを作成しました！ようこそ。","ko":"✅ 계정이 생성되었습니다! 환영합니다.","id":"✅ Akun dibuat! Selamat datang."}
T["donnees_protegees"] = {"fr":"🔒 Tes données sont protégées. Ton mot de passe est chiffré, nous ne pouvons jamais le lire.","en":"🔒 Your data is protected. Your password is encrypted, we can never read it.","es":"🔒 Tus datos están protegidos. Tu contraseña está cifrada, nunca podemos leerla.","pt":"🔒 Seus dados estão protegidos. Sua senha é criptografada, nunca podemos lê-la.","zh":"🔒 你的数据受到保护。你的密码已加密，我们无法读取。","ar":"🔒 بياناتك محمية. كلمة مرورك مشفّرة ولا يمكننا قراءتها أبدًا.","ja":"🔒 データは保護されています。パスワードは暗号化され、私たちが読むことはできません。","ko":"🔒 데이터가 보호됩니다. 비밀번호는 암호화되어 저희가 읽을 수 없습니다.","id":"🔒 Datamu terlindungi. Kata sandimu terenkripsi, kami tidak bisa membacanya."}
T["mes_projets"] = {"fr":"📁 Mes projets","en":"📁 My projects","es":"📁 Mis proyectos","pt":"📁 Meus projetos","zh":"📁 我的项目","ar":"📁 مشاريعي","ja":"📁 マイプロジェクト","ko":"📁 내 프로젝트","id":"📁 Proyek saya"}
T["btn_premium"] = {"fr":"⭐ Passer au Premium","en":"⭐ Go Premium","es":"⭐ Hazte Premium","pt":"⭐ Seja Premium","zh":"⭐ 升级高级会员","ar":"⭐ اشترك في بريميوم","ja":"⭐ プレミアムにする","ko":"⭐ 프리미엄 전환","id":"⭐ Jadi Premium"}

def t(cle, lang):
    """Retourne la traduction d'une clé, avec repli sur le français."""
    v = T.get(cle, {})
    return v.get(lang, v.get("fr", cle))


# =============================================================================
# FUSION des langues supplémentaires (japonais, coréen, indonésien)
# =============================================================================
try:
    from pays_i18n import LANGUES_PLUS, T_PLUS, PAYS_LANGUE_PLUS
    LANGUES.update(LANGUES_PLUS)
    PAYS_LANGUE.update(PAYS_LANGUE_PLUS)
    for cle, trads in T_PLUS.items():
        if cle in T:
            T[cle].update(trads)
        else:
            T[cle] = trads
except ImportError:
    pass

T["contact_titre"] = {"fr":"📬 Nous contacter","en":"📬 Contact us","es":"📬 Contáctanos","pt":"📬 Fale conosco","zh":"📬 联系我们","ar":"📬 اتصل بنا","ja":"📬 お問い合わせ","ko":"📬 문의하기","id":"📬 Hubungi kami"}
T["contact_texte"] = {"fr":"Une question sur ton projet ? Écris-nous, on répond vite.","en":"A question about your project? Write to us, we reply fast.","es":"¿Una pregunta sobre tu proyecto? Escríbenos, respondemos rápido.","pt":"Uma dúvida sobre seu projeto? Escreva, respondemos rápido.","zh":"对你的项目有疑问？给我们留言，我们会尽快回复。","ar":"سؤال حول مشروعك؟ راسلنا، نرد بسرعة.","ja":"プロジェクトについて質問がありますか？お気軽にご連絡ください。","ko":"프로젝트에 대해 궁금한 점이 있나요? 연락 주시면 빠르게 답변드립니다.","id":"Ada pertanyaan tentang proyekmu? Tulis kepada kami, kami balas cepat."}

T["demarches"] = {"fr":"📋 Mes démarches","en":"📋 My procedures","es":"📋 Mis trámites","pt":"📋 Meus trâmites","zh":"📋 我的办理进度","ar":"📋 إجراءاتي","ja":"📋 進行中の手続き","ko":"📋 진행 중인 절차","id":"📋 Proses saya"}
T["gestion_dossiers"] = {"fr":"🛠 Gestion des dossiers","en":"🛠 Case management","es":"🛠 Gestión de expedientes","pt":"🛠 Gestão de dossiês","zh":"🛠 档案管理","ar":"🛠 إدارة الملفات","ja":"🛠 案件管理","ko":"🛠 파일 관리","id":"🛠 Manajemen berkas"}
T["aucune_demarche"] = {"fr":"Aucune démarche en cours. Quand tu nous confies un service, il apparaît ici avec sa progression.","en":"No procedure in progress. When you entrust us with a service, it appears here with its progress.","es":"Ningún trámite en curso. Cuando nos confíes un servicio, aparecerá aquí con su progreso.","pt":"Nenhum trâmite em andamento. Quando você nos confiar um serviço, ele aparecerá aqui com o progresso.","zh":"暂无进行中的办理。当你委托我们服务后，进度会显示在这里。","ar":"لا توجد إجراءات جارية. عندما تعهد إلينا بخدمة، ستظهر هنا مع تقدمها.","ja":"進行中の手続きはありません。サービスをご依頼いただくと、進捗がここに表示されます。","ko":"진행 중인 절차가 없습니다. 서비스를 맡기시면 진행 상황이 여기에 표시됩니다.","id":"Tidak ada proses berjalan. Saat kamu mempercayakan layanan, progresnya muncul di sini."}
T["msg_equipe"] = {"fr":"💬 Message de l'équipe :","en":"💬 Message from the team:","es":"💬 Mensaje del equipo:","pt":"💬 Mensagem da equipe:","zh":"💬 团队留言：","ar":"💬 رسالة الفريق:","ja":"💬 チームからのメッセージ：","ko":"💬 팀 메시지:","id":"💬 Pesan tim:"}
T["ouvert_le"] = {"fr":"Ouvert le","en":"Opened on","es":"Abierto el","pt":"Aberto em","zh":"开启于","ar":"فُتح في","ja":"開始日","ko":"개설일","id":"Dibuka pada"}
T["maj_le"] = {"fr":"dernière mise à jour","en":"last updated","es":"última actualización","pt":"última atualização","zh":"最近更新","ar":"آخر تحديث","ja":"最終更新","ko":"마지막 업데이트","id":"pembaruan terakhir"}
T["statut_recu"] = {"fr":"📥 Reçu","en":"📥 Received","es":"📥 Recibido","pt":"📥 Recebido","zh":"📥 已接收","ar":"📥 تم الاستلام","ja":"📥 受付済み","ko":"📥 접수됨","id":"📥 Diterima"}
T["statut_analyse"] = {"fr":"🔎 En analyse","en":"🔎 Under review","es":"🔎 En análisis","pt":"🔎 Em análise","zh":"🔎 审核中","ar":"🔎 قيد الدراسة","ja":"🔎 審査中","ko":"🔎 검토 중","id":"🔎 Sedang ditinjau"}
T["statut_en_cours"] = {"fr":"⚙️ En cours","en":"⚙️ In progress","es":"⚙️ En curso","pt":"⚙️ Em andamento","zh":"⚙️ 进行中","ar":"⚙️ قيد التنفيذ","ja":"⚙️ 進行中","ko":"⚙️ 진행 중","id":"⚙️ Sedang berjalan"}
T["statut_documents"] = {"fr":"📄 Documents requis","en":"📄 Documents needed","es":"📄 Documentos requeridos","pt":"📄 Documentos necessários","zh":"📄 需提交材料","ar":"📄 مستندات مطلوبة","ja":"📄 書類が必要","ko":"📄 서류 필요","id":"📄 Dokumen diperlukan"}
T["statut_soumis"] = {"fr":"📤 Soumis","en":"📤 Submitted","es":"📤 Enviado","pt":"📤 Enviado","zh":"📤 已提交","ar":"📤 تم التقديم","ja":"📤 提出済み","ko":"📤 제출됨","id":"📤 Terkirim"}
T["statut_termine"] = {"fr":"✅ Terminé","en":"✅ Completed","es":"✅ Completado","pt":"✅ Concluído","zh":"✅ 已完成","ar":"✅ مكتمل","ja":"✅ 完了","ko":"✅ 완료","id":"✅ Selesai"}
T["mon_espace"] = {"fr":"👤 Mon espace","en":"👤 My space","es":"👤 Mi espacio","pt":"👤 Meu espaço","zh":"👤 我的空间","ar":"👤 مساحتي","ja":"👤 マイスペース","ko":"👤 내 공간","id":"👤 Ruang saya"}
T["projets_sauv"] = {"fr":"📁 Mes projets sauvegardés","en":"📁 My saved projects","es":"📁 Mis proyectos guardados","pt":"📁 Meus projetos salvos","zh":"📁 我保存的项目","ar":"📁 مشاريعي المحفوظة","ja":"📁 保存したプロジェクト","ko":"📁 저장된 프로젝트","id":"📁 Proyek tersimpan"}
T["aucun_projet"] = {"fr":"Tu n'as pas encore de projet sauvegardé. Lance une recherche ci-dessous !","en":"No saved projects yet. Start a search below!","es":"Aún no tienes proyectos guardados. ¡Inicia una búsqueda abajo!","pt":"Você ainda não tem projetos salvos. Inicie uma busca abaixo!","zh":"你还没有保存的项目。在下方开始搜索吧！","ar":"ليس لديك مشاريع محفوظة بعد. ابدأ بحثًا أدناه!","ja":"保存されたプロジェクトはまだありません。下から検索を始めましょう！","ko":"저장된 프로젝트가 없습니다. 아래에서 검색을 시작하세요!","id":"Belum ada proyek tersimpan. Mulai pencarian di bawah!"}
T["retour_recherche"] = {"fr":"← Retour à la recherche","en":"← Back to search","es":"← Volver a la búsqueda","pt":"← Voltar à busca","zh":"← 返回搜索","ar":"← العودة إلى البحث","ja":"← 検索に戻る","ko":"← 검색으로 돌아가기","id":"← Kembali ke pencarian"}
T["cree_le"] = {"fr":"créé le","en":"created on","es":"creado el","pt":"criado em","zh":"创建于","ar":"أُنشئ في","ja":"作成日","ko":"생성일","id":"dibuat pada"}
T["mode_test_info"] = {"fr":"🧪 Mode test : paiements simulés.","en":"🧪 Test mode: simulated payments.","es":"🧪 Modo prueba: pagos simulados.","pt":"🧪 Modo teste: pagamentos simulados.","zh":"🧪 测试模式：模拟支付。","ar":"🧪 وضع الاختبار: مدفوعات محاكاة.","ja":"🧪 テストモード：決済はシミュレーションです。","ko":"🧪 테스트 모드: 결제는 시뮬레이션입니다.","id":"🧪 Mode uji: pembayaran simulasi."}
T["btn_choisir"] = {"fr":"Choisir","en":"Choose","es":"Elegir","pt":"Escolher","zh":"选择","ar":"اختر","ja":"選ぶ","ko":"선택","id":"Pilih"}
T["jours"] = {"fr":"jours","en":"days","es":"días","pt":"dias","zh":"天","ar":"يوم","ja":"日間","ko":"일","id":"hari"}


# --- Surcouches + repli de langue UNIVERSEL (traduire_i18n v2) ----------------
# 1) data/i18n/<lg>.json surcharge T (traductions generees ou corrigees a la
#    main) ; 2) toute langue de LANGUES absente d'une entree herite du
#    francais. Ajouter une langue ne peut plus faire planter l'application.
def _charger_surcouches():
    import json as _json
    from pathlib import Path as _P
    for _base in (_P("data") / "i18n",
                  _P(__file__).resolve().parents[2] / "data" / "i18n"):
        try:
            fichiers = sorted(_base.glob("*.json"))
        except Exception:
            continue
        for _f in fichiers:
            try:
                _lg = _f.stem
                for _cle, _val in _json.loads(
                        _f.read_text(encoding="utf-8")).items():
                    if _cle in T and isinstance(T[_cle], dict):
                        T[_cle][_lg] = _val
            except Exception:
                pass
        if fichiers:
            break


def _completer_langues():
    try:
        for _val in T.values():
            if isinstance(_val, dict) and "fr" in _val:
                for _lg in LANGUES:
                    _val.setdefault(_lg, _val["fr"])
    except Exception:
        pass


_charger_surcouches()
_completer_langues()

T["sauver_projet_btn"] = {"fr":"Sauvegarder ce projet","en":"Save this project","es":"Guardar este proyecto","pt":"Guardar este projeto","zh":"保存此项目","ar":"احفظ هذا المشروع","ja":"このプロジェクトを保存","ko":"이 프로젝트 저장","id":"Simpan proyek ini"}
T["projet_sauve_ok"] = {"fr":"Projet sauvegarde ! Retrouvez-le dans Mes projets.","en":"Project saved! Find it in My projects.","es":"Proyecto guardado!","pt":"Projeto guardado! Encontre-o em Meus projetos.","zh":"项目已保存！","ar":"تم حفظ المشروع!","ja":"プロジェクトを保存しました！","ko":"프로젝트가 저장되었습니다!","id":"Proyek disimpan!"}
T["connecte_pour_sauver"] = {"fr":"Connectez-vous pour sauvegarder ce projet.","en":"Log in to save this project.","es":"Inicia sesion para guardar este proyecto.","pt":"Inicie sessao para guardar este projeto.","zh":"登录以保存此项目。","ar":"سجل الدخول لحفظ هذا المشروع.","ja":"ログインして保存。","ko":"로그인하여 저장하세요.","id":"Masuk untuk menyimpan proyek ini."}
