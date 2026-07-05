# =============================================================================
# pays_i18n.py — Noms des pays traduits + ajout des langues JA/KO/ID
# Complète i18n.py. Importé par ui.py.
# =============================================================================

# Langues ajoutées (drapeau + nom natif)
LANGUES_PLUS = {
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "id": "🇮🇩 Indonesia",
}

# --- Traduction des libellés d'interface pour les 3 langues ajoutées ---
# (mêmes clés que i18n.T ; complète ce qui manque)
T_PLUS = {
 "tagline": {"ja":"世界へのあなたの軌道","ko":"세계로 향한 당신의 궤도","id":"Lintasanmu menuju dunia"},
 "q_origine": {"ja":"🌍 出身国","ko":"🌍 출신 국가","id":"🌍 Negara asalmu"},
 "q_dest": {"ja":"🎯 留学先の国","ko":"🎯 목적지 국가","id":"🎯 Negara tujuan"},
 "q_type": {"ja":"📌 プロジェクトの種類","ko":"📌 프로젝트 유형","id":"📌 Jenis proyek"},
 "q_niveau": {"ja":"🎓 目標レベル","ko":"🎓 목표 수준","id":"🎓 Tingkat yang dituju"},
 "q_domaine": {"ja":"📚 専攻分野","ko":"📚 학습 분야","id":"📚 Bidang studi"},
 "choisir": {"ja":"選択…","ko":"선택…","id":"Pilih…"},
 "intro": {"ja":"👆 4つの質問に答えてください。詳しい進路がここに即座に表示されます。",
           "ko":"👆 4가지 질문에 답하세요. 상세한 경로가 여기에 즉시 표시됩니다.",
           "id":"👆 Jawab 4 pertanyaan: jalurmu yang terperinci langsung muncul di sini."},
 "start_from": {"ja":"✨ プロジェクトを始めよう","ko":"✨ 프로젝트를 시작하세요","id":"✨ Mulai proyekmu dari"},
 "budget": {"ja":"💶 証明が必要な資金：","ko":"💶 증명해야 할 자금：","id":"💶 Dana yang harus dibuktikan:"},
 "travail": {"ja":"⚖️ 学生の就労：","ko":"⚖️ 학생 근로：","id":"⚖️ Kerja mahasiswa:"},
 "apres": {"ja":"🎯 卒業後：","ko":"🎯 졸업 후：","id":"🎯 Setelah lulus:"},
 "chemin": {"ja":"🗺️ ステップごとの進路","ko":"🗺️ 단계별 경로","id":"🗺️ Jalurmu, langkah demi langkah"},
 "etape": {"ja":"ステップ","ko":"단계","id":"Langkah"},
 "lien_officiel": {"ja":"🔗 公式リンク","ko":"🔗 공식 링크","id":"🔗 Tautan resmi"},
 "aide_etape": {"ja":"🤝 このステップで手伝いが必要ですか？お任せください",
                "ko":"🤝 이 단계에 도움이 필요하세요? 저희가 처리합니다",
                "id":"🤝 Butuh bantuan untuk langkah ini? Kami urus"},
 "portail": {"ja":"🌐 公式ポータル —","ko":"🌐 공식 포털 —","id":"🌐 Portal resmi —"},
 "bourses_pour_toi": {"ja":"💰 あなた向けの奨学金","ko":"💰 당신을 위한 장학금","id":"💰 Beasiswa untukmu"},
 "accompagne": {"ja":"🤝 最後までサポートします：","ko":"🤝 끝까지 함께합니다：","id":"🤝 Kami dampingi kamu hingga"},
 "accompagne_desc": {"ja":"任せたい手続きを選んでください。私たちのチームが対応し、あなたは各段階で主導権を保てます。",
                     "ko":"위임하고 싶은 절차를 선택하세요. 저희 팀이 처리하며, 각 단계에서 당신이 주도권을 유지합니다.",
                     "id":"Pilih langkah yang ingin kamu delegasikan — tim kami menanganinya, kamu tetap memegang kendali di setiap tahap."},
 "form_titre": {"ja":"📩 あなたのプロジェクトを教えてください — 24時間以内に返信",
                "ko":"📩 프로젝트에 대해 알려주세요 — 24시간 이내 답변",
                "id":"📩 Ceritakan proyekmu — balasan dalam 24 jam"},
 "nom": {"ja":"氏名","ko":"성명","id":"Nama lengkapmu"},
 "contact": {"ja":"WhatsApp またはメール","ko":"WhatsApp 또는 이메일","id":"WhatsApp atau email"},
 "service_interet": {"ja":"ご希望のサービス","ko":"관심 있는 서비스","id":"Layanan yang kamu minati"},
 "projet_2lignes": {"ja":"プロジェクトを2行で（任意）","ko":"프로젝트를 2줄로 (선택)","id":"Proyekmu dalam 2 baris (opsional)"},
 "lancer": {"ja":"🚀 プロジェクトを始める","ko":"🚀 프로젝트 시작하기","id":"🚀 Luncurkan proyekku"},
 "recu": {"ja":"✅ 受け付けました！24〜48時間以内に担当者が個別見積もりをもってご連絡します。",
          "ko":"✅ 접수되었습니다! 상담사가 24~48시간 이내에 맞춤 견적과 함께 연락드립니다.",
          "id":"✅ Diterima! Seorang penasihat akan menghubungimu dalam 24–48 jam dengan penawaran khusus."},
 "champs_requis": {"ja":"氏名と連絡先は必須です。","ko":"성명과 연락처는 필수입니다.","id":"Nama dan kontak wajib diisi."},
 "disclaimer": {"ja":"私たちはあなたと共に手続きを準備・整理します。入学やビザを保証できる者は誰もいません。保証すると約束する者にはご注意ください。",
                "ko":"저희는 당신과 함께 절차를 준비하고 정리합니다. 입학이나 비자를 보장할 수 있는 사람은 없습니다. 보장을 약속하는 사람을 조심하세요.",
                "id":"Kami menyiapkan dan mengatur langkah-langkahmu bersamamu. Tidak ada yang bisa menjamin penerimaan atau visa — waspadai mereka yang menjanjikannya."},
 "langue_label": {"ja":"言語","ko":"언어","id":"Bahasa"},
 "types": {"ja":["課程（入学）","奨学金","インターン／学生アルバイト"],
           "ko":["과정 (입학)","장학금","인턴십 / 학생 아르바이트"],
           "id":["Program (penerimaan)","Beasiswa","Magang / Kerja mahasiswa"]},
 "niveaux": {"ja":["学士","修士","博士","職業訓練","高校生です"],
             "ko":["학사","석사","박사","직업 교육","고등학생입니다"],
             "id":["Sarjana","Magister","Doktor","Pelatihan vokasi","Saya siswa SMA"]},
 "domaines": {"ja":["すべての分野","IT・デジタル","工学","保健・医療","経営・商業・金融","法律・政治学","理学","農業・環境","芸術・デザイン・建築","人文科学","教育","観光・ホスピタリティ"],
              "ko":["모든 분야","IT·디지털","공학","보건·의학","경영·상업·금융","법률·정치학","이학","농업·환경","예술·디자인·건축","인문학","교육","관광·호텔경영"],
              "id":["Semua bidang","TI & digital","Teknik","Kesehatan & kedokteran","Manajemen, bisnis & keuangan","Hukum & ilmu politik","Sains","Pertanian & lingkungan","Seni, desain & arsitektur","Humaniora","Pendidikan","Pariwisata & perhotelan"]},
}

# Pays qui parlent ces langues → détection auto
PAYS_LANGUE_PLUS = {"JP":"ja", "KR":"ko", "ID":"id"}

# =============================================================================
# NOMS DES PAYS traduits. Clé = nom FR (utilisé comme identifiant interne).
# On traduit dans : en, es, pt, zh, ar, ja, ko, id. FR = la clé elle-même.
# Les pays non listés gardent leur nom FR (repli).
# =============================================================================
PAYS = {
 "France": {"en":"France","es":"Francia","pt":"França","zh":"法国","ar":"فرنسا","ja":"フランス","ko":"프랑스","id":"Prancis"},
 "Canada": {"en":"Canada","es":"Canadá","pt":"Canadá","zh":"加拿大","ar":"كندا","ja":"カナダ","ko":"캐나다","id":"Kanada"},
 "États-Unis": {"en":"United States","es":"Estados Unidos","pt":"Estados Unidos","zh":"美国","ar":"الولايات المتحدة","ja":"アメリカ","ko":"미국","id":"Amerika Serikat"},
 "Royaume-Uni": {"en":"United Kingdom","es":"Reino Unido","pt":"Reino Unido","zh":"英国","ar":"المملكة المتحدة","ja":"イギリス","ko":"영국","id":"Inggris"},
 "Allemagne": {"en":"Germany","es":"Alemania","pt":"Alemanha","zh":"德国","ar":"ألمانيا","ja":"ドイツ","ko":"독일","id":"Jerman"},
 "Belgique": {"en":"Belgium","es":"Bélgica","pt":"Bélgica","zh":"比利时","ar":"بلجيكا","ja":"ベルギー","ko":"벨기에","id":"Belgia"},
 "Italie": {"en":"Italy","es":"Italia","pt":"Itália","zh":"意大利","ar":"إيطاليا","ja":"イタリア","ko":"이탈리아","id":"Italia"},
 "Espagne": {"en":"Spain","es":"España","pt":"Espanha","zh":"西班牙","ar":"إسبانيا","ja":"スペイン","ko":"스페인","id":"Spanyol"},
 "Portugal": {"en":"Portugal","es":"Portugal","pt":"Portugal","zh":"葡萄牙","ar":"البرتغال","ja":"ポルトガル","ko":"포르투갈","id":"Portugal"},
 "Pays-Bas": {"en":"Netherlands","es":"Países Bajos","pt":"Países Baixos","zh":"荷兰","ar":"هولندا","ja":"オランダ","ko":"네덜란드","id":"Belanda"},
 "Grèce": {"en":"Greece","es":"Grecia","pt":"Grécia","zh":"希腊","ar":"اليونان","ja":"ギリシャ","ko":"그리스","id":"Yunani"},
 "République tchèque": {"en":"Czech Republic","es":"República Checa","pt":"República Tcheca","zh":"捷克","ar":"التشيك","ja":"チェコ","ko":"체코","id":"Ceko"},
 "Pologne": {"en":"Poland","es":"Polonia","pt":"Polônia","zh":"波兰","ar":"بولندا","ja":"ポーランド","ko":"폴란드","id":"Polandia"},
 "Roumanie": {"en":"Romania","es":"Rumanía","pt":"Romênia","zh":"罗马尼亚","ar":"رومانيا","ja":"ルーマニア","ko":"루마니아","id":"Rumania"},
 "Hongrie": {"en":"Hungary","es":"Hungría","pt":"Hungria","zh":"匈牙利","ar":"المجر","ja":"ハンガリー","ko":"헝가리","id":"Hungaria"},
 "Russie": {"en":"Russia","es":"Rusia","pt":"Rússia","zh":"俄罗斯","ar":"روسيا","ja":"ロシア","ko":"러시아","id":"Rusia"},
 "Turquie": {"en":"Turkey","es":"Turquía","pt":"Turquia","zh":"土耳其","ar":"تركيا","ja":"トルコ","ko":"터키","id":"Turki"},
 "Japon": {"en":"Japan","es":"Japón","pt":"Japão","zh":"日本","ar":"اليابان","ja":"日本","ko":"일본","id":"Jepang"},
 "Corée du Sud": {"en":"South Korea","es":"Corea del Sur","pt":"Coreia do Sul","zh":"韩国","ar":"كوريا الجنوبية","ja":"韓国","ko":"대한민국","id":"Korea Selatan"},
 "Chine": {"en":"China","es":"China","pt":"China","zh":"中国","ar":"الصين","ja":"中国","ko":"중국","id":"Tiongkok"},
 "Inde": {"en":"India","es":"India","pt":"Índia","zh":"印度","ar":"الهند","ja":"インド","ko":"인도","id":"India"},
 "Pakistan": {"en":"Pakistan","es":"Pakistán","pt":"Paquistão","zh":"巴基斯坦","ar":"باكستان","ja":"パキスタン","ko":"파키스탄","id":"Pakistan"},
 "Indonésie": {"en":"Indonesia","es":"Indonesia","pt":"Indonésia","zh":"印度尼西亚","ar":"إندونيسيا","ja":"インドネシア","ko":"인도네시아","id":"Indonesia"},
 "Malaisie": {"en":"Malaysia","es":"Malasia","pt":"Malásia","zh":"马来西亚","ar":"ماليزيا","ja":"マレーシア","ko":"말레이시아","id":"Malaysia"},
 "Thaïlande": {"en":"Thailand","es":"Tailandia","pt":"Tailândia","zh":"泰国","ar":"تايلاند","ja":"タイ","ko":"태국","id":"Thailand"},
 "Australie": {"en":"Australia","es":"Australia","pt":"Austrália","zh":"澳大利亚","ar":"أستراليا","ja":"オーストラリア","ko":"호주","id":"Australia"},
 "Brésil": {"en":"Brazil","es":"Brasil","pt":"Brasil","zh":"巴西","ar":"البرازيل","ja":"ブラジル","ko":"브라질","id":"Brasil"},
 "Maroc": {"en":"Morocco","es":"Marruecos","pt":"Marrocos","zh":"摩洛哥","ar":"المغرب","ja":"モロッコ","ko":"모로코","id":"Maroko"},
 "Tunisie": {"en":"Tunisia","es":"Túnez","pt":"Tunísia","zh":"突尼斯","ar":"تونس","ja":"チュニジア","ko":"튀니지","id":"Tunisia"},
 "Sénégal": {"en":"Senegal","es":"Senegal","pt":"Senegal","zh":"塞内加尔","ar":"السنغال","ja":"セネガル","ko":"세네갈","id":"Senegal"},
 "Rwanda": {"en":"Rwanda","es":"Ruanda","pt":"Ruanda","zh":"卢旺达","ar":"رواندا","ja":"ルワンダ","ko":"르완다","id":"Rwanda"},
 "Ghana": {"en":"Ghana","es":"Ghana","pt":"Gana","zh":"加纳","ar":"غانا","ja":"ガーナ","ko":"가나","id":"Ghana"},
 "Afrique du Sud": {"en":"South Africa","es":"Sudáfrica","pt":"África do Sul","zh":"南非","ar":"جنوب أفريقيا","ja":"南アフリカ","ko":"남아프리카공화국","id":"Afrika Selatan"},
 "Égypte": {"en":"Egypt","es":"Egipto","pt":"Egito","zh":"埃及","ar":"مصر","ja":"エジプト","ko":"이집트","id":"Mesir"},
 "Arabie Saoudite": {"en":"Saudi Arabia","es":"Arabia Saudita","pt":"Arábia Saudita","zh":"沙特阿拉伯","ar":"السعودية","ja":"サウジアラビア","ko":"사우디아라비아","id":"Arab Saudi"},
 "Émirats Arabes Unis": {"en":"United Arab Emirates","es":"Emiratos Árabes Unidos","pt":"Emirados Árabes Unidos","zh":"阿联酋","ar":"الإمارات","ja":"アラブ首長国連邦","ko":"아랍에미리트","id":"Uni Emirat Arab"},
 "Qatar": {"en":"Qatar","es":"Catar","pt":"Catar","zh":"卡塔尔","ar":"قطر","ja":"カタール","ko":"카타르","id":"Qatar"},
 "Suisse": {"en":"Switzerland","es":"Suiza","pt":"Suíça","zh":"瑞士","ar":"سويسرا","ja":"スイス","ko":"스위스","id":"Swiss"},
 "Suède": {"en":"Sweden","es":"Suecia","pt":"Suécia","zh":"瑞典","ar":"السويد","ja":"スウェーデン","ko":"스웨덴","id":"Swedia"},
 "Irlande": {"en":"Ireland","es":"Irlanda","pt":"Irlanda","zh":"爱尔兰","ar":"أيرلندا","ja":"アイルランド","ko":"아일랜드","id":"Irlandia"},
 # Origines supplémentaires fréquentes
 "Gabon": {"en":"Gabon","es":"Gabón","pt":"Gabão","zh":"加蓬","ar":"الغابون","ja":"ガボン","ko":"가봉","id":"Gabon"},
 "Cameroun": {"en":"Cameroon","es":"Camerún","pt":"Camarões","zh":"喀麦隆","ar":"الكاميرون","ja":"カメルーン","ko":"카메룬","id":"Kamerun"},
 "Haïti": {"en":"Haiti","es":"Haití","pt":"Haiti","zh":"海地","ar":"هايتي","ja":"ハイチ","ko":"아이티","id":"Haiti"},
 "Côte d'Ivoire": {"en":"Ivory Coast","es":"Costa de Marfil","pt":"Costa do Marfim","zh":"科特迪瓦","ar":"ساحل العاج","ja":"コートジボワール","ko":"코트디부아르","id":"Pantai Gading"},
 "Congo (RDC)": {"en":"DR Congo","es":"RD del Congo","pt":"RD Congo","zh":"刚果(金)","ar":"الكونغو الديمقراطية","ja":"コンゴ民主共和国","ko":"콩고민주공화국","id":"Kongo (RDK)"},
 "Congo (Brazzaville)": {"en":"Congo","es":"Congo","pt":"Congo","zh":"刚果(布)","ar":"الكونغو","ja":"コンゴ共和国","ko":"콩고공화국","id":"Kongo"},
 "Nigeria": {"en":"Nigeria","es":"Nigeria","pt":"Nigéria","zh":"尼日利亚","ar":"نيجيريا","ja":"ナイジェリア","ko":"나이지리아","id":"Nigeria"},
 "Kenya": {"en":"Kenya","es":"Kenia","pt":"Quênia","zh":"肯尼亚","ar":"كينيا","ja":"ケニア","ko":"케냐","id":"Kenya"},
 "Algérie": {"en":"Algeria","es":"Argelia","pt":"Argélia","zh":"阿尔及利亚","ar":"الجزائر","ja":"アルジェリア","ko":"알제리","id":"Aljazair"},
 "Mali": {"en":"Mali","es":"Malí","pt":"Mali","zh":"马里","ar":"مالي","ja":"マリ","ko":"말리","id":"Mali"},
 "Bénin": {"en":"Benin","es":"Benín","pt":"Benin","zh":"贝宁","ar":"بنين","ja":"ベナン","ko":"베냉","id":"Benin"},
 "Togo": {"en":"Togo","es":"Togo","pt":"Togo","zh":"多哥","ar":"توغو","ja":"トーゴ","ko":"토고","id":"Togo"},
 "Niger": {"en":"Niger","es":"Níger","pt":"Níger","zh":"尼日尔","ar":"النيجر","ja":"ニジェール","ko":"니제르","id":"Niger"},
 "Burkina Faso": {"en":"Burkina Faso","es":"Burkina Faso","pt":"Burquina Faso","zh":"布基纳法索","ar":"بوركينا فاسو","ja":"ブルキナファソ","ko":"부르키나파소","id":"Burkina Faso"},
 "Guinée": {"en":"Guinea","es":"Guinea","pt":"Guiné","zh":"几内亚","ar":"غينيا","ja":"ギニア","ko":"기니","id":"Guinea"},
 "Madagascar": {"en":"Madagascar","es":"Madagascar","pt":"Madagáscar","zh":"马达加斯加","ar":"مدغشقر","ja":"マダガスカル","ko":"마다가스카르","id":"Madagaskar"},
 "Tchad": {"en":"Chad","es":"Chad","pt":"Chade","zh":"乍得","ar":"تشاد","ja":"チャド","ko":"차드","id":"Chad"},
 "Chine ": {"en":"China","es":"China","pt":"China","zh":"中国","ar":"الصين","ja":"中国","ko":"중국","id":"Tiongkok"},
 "Vietnam": {"en":"Vietnam","es":"Vietnam","pt":"Vietnã","zh":"越南","ar":"فيتنام","ja":"ベトナム","ko":"베트남","id":"Vietnam"},
 "Mexique": {"en":"Mexico","es":"México","pt":"México","zh":"墨西哥","ar":"المكسيك","ja":"メキシコ","ko":"멕시코","id":"Meksiko"},
 "Colombie": {"en":"Colombia","es":"Colombia","pt":"Colômbia","zh":"哥伦比亚","ar":"كولومبيا","ja":"コロンビア","ko":"콜롬비아","id":"Kolombia"},
 "Bangladesh": {"en":"Bangladesh","es":"Bangladés","pt":"Bangladesh","zh":"孟加拉国","ar":"بنغلاديش","ja":"バングラデシュ","ko":"방글라데시","id":"Bangladesh"},
 "Népal": {"en":"Nepal","es":"Nepal","pt":"Nepal","zh":"尼泊尔","ar":"نيبال","ja":"ネパール","ko":"네팔","id":"Nepal"},
 "Philippines": {"en":"Philippines","es":"Filipinas","pt":"Filipinas","zh":"菲律宾","ar":"الفلبين","ja":"フィリピン","ko":"필리핀","id":"Filipina"},
 "Ukraine": {"en":"Ukraine","es":"Ucrania","pt":"Ucrânia","zh":"乌克兰","ar":"أوكرانيا","ja":"ウクライナ","ko":"우크라이나","id":"Ukraina"},
}

def nom_pays(nom_fr, lang):
    """Traduit un nom de pays. Repli sur le nom FR si absent."""
    if lang == "fr":
        return nom_fr
    return PAYS.get(nom_fr, {}).get(lang, nom_fr)
