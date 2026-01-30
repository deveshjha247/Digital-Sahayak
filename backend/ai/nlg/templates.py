"""
DS-Talk Templates
=================
100+ Hindi and English templates for natural language generation.
Templates are organized by section and language.
Each section has multiple variations for natural feel.
"""

TEMPLATES = {
    # ===================== JOB SUMMARY =====================
    "job_summary_hi": [
        "{title} का आधिकारिक नोटिस आ चुका है।",
        "{title} भर्ती के लिए सूचना जारी की गई है।",
        "{title} के लिए आवेदन शुरू हो चुके हैं।",
        "{title} की भर्ती का इंतज़ार कर रहे थे? अब मौका है!",
        "{title} भर्ती की जानकारी यहाँ है।",
        "{title} के लिए नोटिफिकेशन जारी हुआ है।",
        "खुशखबरी! {title} के लिए आवेदन मांगे गए हैं।",
        "{title} भर्ती 2025 की पूरी जानकारी देखें।",
        "{title} - नई भर्ती की घोषणा हुई है।",
        "{title} के लिए ऑनलाइन आवेदन का मौका।",
    ],
    
    "job_summary_en": [
        "The official notification for {title} has been released.",
        "A recruitment notice for {title} is out.",
        "Applications have started for {title}.",
        "Were you waiting for {title}? Here's your chance!",
        "Here's the complete information about {title}.",
        "{title} notification has been published.",
        "Good news! Applications invited for {title}.",
        "Complete details of {title} Recruitment 2025.",
        "{title} - New recruitment announced.",
        "Online application opportunity for {title}.",
    ],
    
    # ===================== SCHEME SUMMARY =====================
    "scheme_summary_hi": [
        "{title} योजना के बारे में जानकारी।",
        "{title} - सरकारी योजना की पूरी जानकारी।",
        "{title} योजना का लाभ कैसे उठाएं, जानें यहाँ।",
        "{title} - पात्रता और आवेदन प्रक्रिया।",
        "{title} योजना के तहत मिलने वाले फायदे।",
        "क्या आप {title} के लिए पात्र हैं? जानें।",
        "{title} - ऐसे करें आवेदन।",
        "{title} योजना की ताज़ा जानकारी।",
    ],
    
    "scheme_summary_en": [
        "Information about {title} scheme.",
        "{title} - Complete details of the government scheme.",
        "How to avail benefits of {title}, learn here.",
        "{title} - Eligibility and application process.",
        "Benefits available under {title} scheme.",
        "Are you eligible for {title}? Find out.",
        "{title} - How to apply.",
        "Latest information about {title} scheme.",
    ],
    
    # ===================== RESULT SUMMARY =====================
    "result_summary_hi": [
        "{title} का रिजल्ट घोषित हो चुका है!",
        "{title} - परिणाम आ गया है।",
        "बधाई हो! {title} के नतीजे जारी।",
        "{title} का परिणाम अब उपलब्ध है।",
        "{title} - मेरिट लिस्ट देखें।",
        "इंतज़ार खत्म! {title} रिजल्ट आउट।",
        "{title} के परीक्षा परिणाम घोषित।",
        "{title} - अपना रिजल्ट यहाँ चेक करें।",
    ],
    
    "result_summary_en": [
        "The result for {title} has been declared!",
        "{title} - Results are out.",
        "Congratulations! {title} results announced.",
        "{title} result is now available.",
        "{title} - Check the merit list.",
        "Wait is over! {title} result out.",
        "{title} examination results declared.",
        "{title} - Check your result here.",
    ],
    
    # ===================== DATES =====================
    "date_hi": [
        "आवेदन की अंतिम तिथि {last_date} है।",
        "फॉर्म भरने की आख़िरी तारीख़ {last_date} तय की गई है।",
        "{last_date} तक आवेदन किया जा सकता है।",
        "जल्दी करें! अंतिम तिथि {last_date} है।",
        "आवेदन {last_date} तक स्वीकार किए जाएंगे।",
        "लास्ट डेट: {last_date} - देर न करें!",
        "{last_date} से पहले आवेदन अवश्य करें।",
        "समय सीमा: {last_date} तक।",
    ],
    
    "date_en": [
        "The last date to apply is {last_date}.",
        "Application deadline has been set as {last_date}.",
        "You can apply till {last_date}.",
        "Hurry! Last date is {last_date}.",
        "Applications will be accepted until {last_date}.",
        "Last date: {last_date} - Don't delay!",
        "Make sure to apply before {last_date}.",
        "Deadline: {last_date}.",
    ],
    
    "start_date_hi": [
        "आवेदन {start_date} से शुरू हो चुके हैं।",
        "फॉर्म {start_date} से भरे जा रहे हैं।",
        "{start_date} से ऑनलाइन आवेदन शुरू।",
    ],
    
    "start_date_en": [
        "Applications started from {start_date}.",
        "Forms are being filled since {start_date}.",
        "Online application began on {start_date}.",
    ],
    
    "exam_date_hi": [
        "परीक्षा तिथि: {exam_date}",
        "एग्जाम {exam_date} को होगा।",
        "{exam_date} को परीक्षा आयोजित की जाएगी।",
    ],
    
    "exam_date_en": [
        "Exam date: {exam_date}",
        "Examination will be held on {exam_date}.",
        "The exam is scheduled for {exam_date}.",
    ],
    
    # ===================== ELIGIBILITY =====================
    "eligibility_hi": [
        "पात्रता शर्तें: {eligibility}",
        "आवेदन के लिए योग्यता: {eligibility}",
        "कौन आवेदन कर सकता है: {eligibility}",
        "पात्रता मानदंड इस प्रकार हैं: {eligibility}",
        "आवश्यक योग्यता: {eligibility}",
        "इन शर्तों को पूरा करने वाले आवेदन कर सकते हैं: {eligibility}",
    ],
    
    "eligibility_en": [
        "Eligibility criteria: {eligibility}",
        "Qualification for application: {eligibility}",
        "Who can apply: {eligibility}",
        "Eligibility requirements are: {eligibility}",
        "Required qualification: {eligibility}",
        "Candidates meeting these criteria can apply: {eligibility}",
    ],
    
    "age_limit_hi": [
        "आयु सीमा: {min_age} से {max_age} वर्ष।",
        "उम्र {min_age}-{max_age} साल होनी चाहिए।",
        "न्यूनतम आयु {min_age} और अधिकतम {max_age} वर्ष।",
    ],
    
    "age_limit_en": [
        "Age limit: {min_age} to {max_age} years.",
        "Age should be between {min_age}-{max_age} years.",
        "Minimum age {min_age} and maximum {max_age} years.",
    ],
    
    # ===================== DOCUMENTS =====================
    "documents_hi": [
        "आवश्यक दस्तावेज़: {documents}",
        "ये कागज़ात रखें तैयार: {documents}",
        "आवेदन के लिए चाहिए: {documents}",
        "ज़रूरी डॉक्यूमेंट्स: {documents}",
        "इन दस्तावेज़ों की ज़रूरत होगी: {documents}",
    ],
    
    "documents_en": [
        "Required documents: {documents}",
        "Keep these papers ready: {documents}",
        "You will need: {documents}",
        "Necessary documents: {documents}",
        "These documents will be required: {documents}",
    ],
    
    # ===================== FEES =====================
    "fees_hi": [
        "आवेदन शुल्क: ₹{govt_fee} (सरकारी) + ₹{service_fee} (सेवा शुल्क) = कुल ₹{total}",
        "फीस: ₹{total} (₹{govt_fee} + ₹{service_fee} सर्विस चार्ज)",
        "आवेदन करने का खर्च: ₹{total} (सरकारी फीस ₹{govt_fee} + ₹{service_fee})",
        "कुल शुल्क ₹{total} है जिसमें ₹{govt_fee} सरकारी और ₹{service_fee} सेवा शुल्क शामिल है।",
        "भुगतान: ₹{total} (फॉर्म फीस + सर्विस चार्ज)",
    ],
    
    "fees_en": [
        "Application fee: ₹{govt_fee} (government) + ₹{service_fee} (service charge) = Total ₹{total}",
        "Fee: ₹{total} (₹{govt_fee} + ₹{service_fee} service charge)",
        "Cost to apply: ₹{total} (govt fee ₹{govt_fee} + ₹{service_fee})",
        "Total fee is ₹{total} including ₹{govt_fee} government and ₹{service_fee} service charge.",
        "Payment: ₹{total} (form fee + service charge)",
    ],
    
    "fees_category_hi": [
        "श्रेणी के अनुसार शुल्क: सामान्य ₹{general}, OBC ₹{obc}, SC/ST ₹{sc_st}",
        "कैटेगरी वाइज फीस अलग-अलग है।",
    ],
    
    "fees_category_en": [
        "Category-wise fee: General ₹{general}, OBC ₹{obc}, SC/ST ₹{sc_st}",
        "Fee varies by category.",
    ],
    
    # ===================== VACANCIES =====================
    "vacancies_hi": [
        "कुल {vacancies} पदों पर भर्ती होगी।",
        "{vacancies} रिक्तियाँ भरी जाएंगी।",
        "पदों की संख्या: {vacancies}",
        "कुल {vacancies} सीटें उपलब्ध हैं।",
    ],
    
    "vacancies_en": [
        "Recruitment for total {vacancies} posts.",
        "{vacancies} vacancies will be filled.",
        "Number of posts: {vacancies}",
        "Total {vacancies} seats available.",
    ],
    
    # ===================== LINKS =====================
    "links_hi": [
        "आधिकारिक लिंक: {link}",
        "यहाँ से आवेदन करें: {link}",
        "ऑफिशियल वेबसाइट: {link}",
        "अधिक जानकारी के लिए: {link}",
        "सीधा लिंक: {link}",
    ],
    
    "links_en": [
        "Official link: {link}",
        "Apply here: {link}",
        "Official website: {link}",
        "For more information: {link}",
        "Direct link: {link}",
    ],
    
    # ===================== CALL TO ACTION =====================
    "cta_hi": [
        "जल्द से जल्द आवेदन करें!",
        "इस मौके को मिस न करें, अभी अप्लाई करें।",
        "आवेदन करने में देर न करें।",
        "तैयारी शुरू करें और समय पर फॉर्म भरें।",
        "सभी ज़रूरी जानकारी लेकर आवेदन करें।",
        "शुभकामनाएं! अपना फॉर्म समय पर जमा करें।",
        "डिजिटल सहायक की मदद से आसानी से अप्लाई करें।",
        "किसी भी सवाल के लिए हमसे पूछें।",
    ],
    
    "cta_en": [
        "Apply as soon as possible!",
        "Don't miss this opportunity, apply now.",
        "Don't delay in applying.",
        "Start preparing and fill the form on time.",
        "Gather all necessary information and apply.",
        "Best wishes! Submit your form on time.",
        "Apply easily with Digital Sahayak's help.",
        "Ask us for any questions.",
    ],
    
    # ===================== NOT FOUND =====================
    "not_found_hi": [
        "माफ़ कीजिए, इस बारे में विश्वसनीय जानकारी नहीं मिली।",
        "अभी इस विषय पर आधिकारिक जानकारी उपलब्ध नहीं है।",
        "कृपया आधिकारिक वेबसाइट पर जाँच करें।",
        "इस समय इसकी जानकारी हमारे पास नहीं है।",
    ],
    
    "not_found_en": [
        "Sorry, reliable information about this was not found.",
        "Official information on this topic is not available right now.",
        "Please check the official website.",
        "We don't have information about this at the moment.",
    ],
    
    # ===================== STATE/DEPARTMENT =====================
    "state_hi": [
        "राज्य: {state}",
        "यह {state} की भर्ती है।",
        "{state} राज्य के उम्मीदवारों के लिए।",
    ],
    
    "state_en": [
        "State: {state}",
        "This is a {state} recruitment.",
        "For candidates of {state} state.",
    ],
    
    "department_hi": [
        "विभाग: {department}",
        "यह {department} विभाग की भर्ती है।",
        "{department} में नौकरी का मौका।",
    ],
    
    "department_en": [
        "Department: {department}",
        "This is a {department} department recruitment.",
        "Job opportunity in {department}.",
    ],
    
    # ===================== ADMIT CARD =====================
    "admit_card_hi": [
        "{title} का एडमिट कार्ड जारी हो चुका है।",
        "हॉल टिकट {title} के लिए डाउनलोड करें।",
        "{title} - एडमिट कार्ड अब उपलब्ध है।",
        "जल्दी से अपना एडमिट कार्ड डाउनलोड करें।",
    ],
    
    "admit_card_en": [
        "Admit card for {title} has been released.",
        "Download hall ticket for {title}.",
        "{title} - Admit card is now available.",
        "Download your admit card quickly.",
    ],
    
    # ===================== ANSWER KEY =====================
    "answer_key_hi": [
        "{title} की उत्तर कुंजी जारी हो गई है।",
        "आंसर की {title} के लिए उपलब्ध।",
        "{title} - अपने उत्तर मिलाएं।",
    ],
    
    "answer_key_en": [
        "Answer key for {title} has been released.",
        "Answer key available for {title}.",
        "{title} - Match your answers.",
    ],
    
    # ===================== DISCLAIMER =====================
    "disclaimer_hi": [
        "📌 नोट: यह जानकारी उपलब्ध स्रोतों से ली गई है। आवेदन से पहले आधिकारिक वेबसाइट पर ज़रूर जाँचें।",
        "⚠️ कृपया आधिकारिक नोटिफिकेशन अवश्य देखें।",
    ],
    
    "disclaimer_en": [
        "📌 Note: This information is from available sources. Please verify on official website before applying.",
        "⚠️ Please check the official notification.",
    ],
}

# ===================== BULLET TEMPLATES =====================

BULLET_TEMPLATES = {
    "bullet_hi": "• {item}",
    "bullet_en": "• {item}",
    "numbered_hi": "{num}. {item}",
    "numbered_en": "{num}. {item}",
}

# ===================== CONNECTOR TEMPLATES =====================

CONNECTORS = {
    "hi": ["इसके अलावा,", "साथ ही,", "और,", "तथा,"],
    "en": ["Additionally,", "Also,", "Moreover,", "Furthermore,"],
}
