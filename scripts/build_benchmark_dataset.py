"""
Script to build and validate data/evaluation/benchmark_dataset_v1.json.
Guarantees exact character offsets for ground truth spans and enforces
strict leakage prevention across calibration and held-out evaluation splits.
"""

import json
from pathlib import Path
from plagiarism.evaluation.dataset_loader import load_benchmark_dataset

def build_dataset():
    data = {
        "dataset_id": "BENCHMARK-MULTILINGUAL-V1",
        "version": "1.0.0",
        "created_at": "2026-10-14T20:30:00Z",
        "description": "Scientific benchmarking dataset for multilingual plagiarism detection covering English, Hindi, and Telugu. Partitioned into strict calibration and held-out evaluation splits.",
        "languages": ["en", "hi", "te"],
        "examples": [
            # =========================================================================
            # CALIBRATION SPLIT (20 examples: 11 positives, 9 negatives)
            # =========================================================================
            {
                "id": "CALIB-01",
                "suspicious_text": "Photosynthesis in green plants converts light energy into chemical energy stored in carbohydrate molecules such as glucose.",
                "source_text": "Photosynthesis in green plants converts light energy into chemical energy stored in carbohydrate molecules such as glucose.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "exact",
                "is_plagiarism": True,
                "difficulty": "easy",
                "domain": "biology",
                "provenance": "OpenStax Biology 2e",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 122,
                        "text": "Photosynthesis in green plants converts light energy into chemical energy stored in carbohydrate molecules such as glucose.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Verbatim copy of biological definition."
            },
            {
                "id": "CALIB-02",
                "suspicious_text": "Modern deep learning architectures transformed natural language processing by utilizing attention layers and self-supervised training strategies.",
                "source_text": "Deep neural networks have revolutionized natural language understanding through transformer attention mechanisms and self-supervised pretraining.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "computer_science",
                "provenance": "Vaswani et al. Attention Is All You Need",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 147,
                        "text": "Modern deep learning architectures transformed natural language processing by utilizing attention layers and self-supervised training strategies.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Structural paraphrase with synonymous technical substitutions in English."
            },
            {
                "id": "CALIB-03",
                "suspicious_text": "Preliminary research shows promising results. However, plant chloroplasts harness the power of sunlight to generate vital organic sugars and chemical energy stores.",
                "source_text": "Photosynthesis in green plants converts light energy into chemical energy stored in carbohydrate molecules such as glucose.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "near_exact",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "botany",
                "provenance": "Plant Physiology Journal",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 47,
                        "end_char": 165,
                        "text": "plant chloroplasts harness the power of sunlight to generate vital organic sugars and chemical energy stores.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Partial plagiarized span embedded inside novel opening sentence."
            },
            {
                "id": "CALIB-04",
                "suspicious_text": "अनुसंधान में दूसरों के विचारों को बिना श्रेय दिए उपयोग करना शैक्षणिक सत्यनिष्ठा और आचार संहिता का सीधा हनन है।",
                "source_text": "साहित्यिक चोरी शैक्षणिक अखंडता और अनुसंधान के मानकों का उल्लंघन करती है।",
                "suspicious_language": "hi",
                "source_language": "hi",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "academic_ethics",
                "provenance": "UGC Academic Integrity Guidelines (Hindi)",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 111,
                        "text": "अनुसंधान में दूसरों के विचारों को बिना श्रेय दिए उपयोग करना शैक्षणिक सत्यनिष्ठा और आचार संहिता का सीधा हनन है।",
                        "language": "hi",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Hindi academic ethics paraphrase with Devanagari phraseology."
            },
            {
                "id": "CALIB-05",
                "suspicious_text": "धरती के औसत तापमान में बढ़ोत्तरी से ग्लेशियरों का पिघलना पर्यावरण संकट को और अधिक गंभीर बना रहा है।",
                "source_text": "जलवायु परिवर्तन के कारण वैश्विक तापमान में निरंतर वृद्धि हो रही है, जिससे हिमनद तेजी से पिघल रहे हैं।",
                "suspicious_language": "hi",
                "source_language": "hi",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "climatology",
                "provenance": "IPCC Hindi Regional Report",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 100,
                        "text": "धरती के औसत तापमान में बढ़ोत्तरी से ग्लेशियरों का पिघलना पर्यावरण संकट को और अधिक गंभीर बना रहा है।",
                        "language": "hi",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Hindi climate change cause-and-effect paraphrase."
            },
            {
                "id": "CALIB-06",
                "suspicious_text": "నేటి సాంకేతిక మార్పులకు ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ మరియు మెషిన్ లెర్నింగ్ కీలక చోదక శక్తులుగా మారాయి.",
                "source_text": "కృత్రిమ మేధస్సు మరియు యంత్ర అభ్యాసం ఆధునిక సాంకేతిక విప్లవానికి పునాదిగా నిలుస్తున్నాయి.",
                "suspicious_language": "te",
                "source_language": "te",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "computer_science",
                "provenance": "Telugu Tech Review",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 98,
                        "text": "నేటి సాంకేతిక మార్పులకు ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ మరియు మెషిన్ లెర్నింగ్ కీలక చోదక శక్తులుగా మారాయి.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Telugu artificial intelligence technological revolution paraphrase."
            },
            {
                "id": "CALIB-07",
                "suspicious_text": "విశ్వవిద్యాలయాల గౌరవం మరియు వైజ్ఞానిక ప్రమాణాలు పరిశోధనలో చూపించే నైతిక విలువలపైనే ఆధారపడి ఉంటాయి.",
                "source_text": "పరిశోధనా రంగంలో నిజాయితీ విద్యాసంస్థల ప్రతిష్టకు అత్యంత ఆవశ్యకమైన ప్రమాణం.",
                "suspicious_language": "te",
                "source_language": "te",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "academic_ethics",
                "provenance": "UGC Telugu Guidelines",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 97,
                        "text": "విశ్వవిద్యాలయాల గౌరవం మరియు వైజ్ఞానిక ప్రమాణాలు పరిశోధనలో చూపించే నైతిక విలువలపైనే ఆధారపడి ఉంటాయి.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Telugu academic ethics paraphrase."
            },
            {
                "id": "CALIB-08",
                "suspicious_text": "क्वांटम कंप्यूटिंग जटिल गणितीय समस्याओं को हल करने के लिए क्वांटम सुपरपोजिशन और एंटैंगलमेंट का उपयोग करती है।",
                "source_text": "Quantum computing utilizes quantum superposition and entanglement to solve complex mathematical problems.",
                "suspicious_language": "hi",
                "source_language": "en",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "physics",
                "provenance": "Nielsen and Chuang Quantum Computation",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 109,
                        "text": "क्वांटम कंप्यूटिंग जटिल गणितीय समस्याओं को हल करने के लिए क्वांटम सुपरपोजिशन और एंटैंगलमेंट का उपयोग करती है।",
                        "language": "hi",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Direct English to Hindi translation of quantum physics passage."
            },
            {
                "id": "CALIB-09",
                "suspicious_text": "Natural language processing enables computational systems to comprehend and generate human languages effectively.",
                "source_text": "प्राकृतिक भाषा प्रसंस्करण कंप्यूटरों को मानव भाषा को समझने और उत्पन्न करने में सक्षम बनाता है।",
                "suspicious_language": "en",
                "source_language": "hi",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "computer_science",
                "provenance": "Jurafsky and Martin SLP",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 114,
                        "text": "Natural language processing enables computational systems to comprehend and generate human languages effectively.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Hindi to English translation of NLP concepts."
            },
            {
                "id": "CALIB-10",
                "suspicious_text": "సౌర ఫలకాలు ఫోటోవోల్టాయిక్ కణాల ద్వారా సూర్యకాంతిని పునరుత్పాదక విద్యుత్ శక్తిగా మారుస్తాయి.",
                "source_text": "Solar panels convert incident sunlight into renewable electrical energy using photovoltaic cells.",
                "suspicious_language": "te",
                "source_language": "en",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "renewable_energy",
                "provenance": "Clean Energy Research Group",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 89,
                        "text": "సౌర ఫలకాలు ఫోటోవోల్టాయిక్ కణాల ద్వారా సూర్యకాంతిని పునరుత్పాదక విద్యుత్ శక్తిగా మారుస్తాయి.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "English to Telugu translation of solar power principles."
            },
            {
                "id": "CALIB-11",
                "suspicious_text": "సాఫ్ట్‌వేర్ ఇంజనీరింగ్‌లో కోడ్ నాణ్యత మరియు నిరంతర పరీక్షలు చాలా కీలకమైన ప్రక్రియలు.",
                "source_text": "सॉफ़्टवेयर इंजीनियरिंग में कोड की गुणवत्ता और परीक्षण अत्यंत महत्वपूर्ण प्रक्रियाएं हैं।",
                "suspicious_language": "te",
                "source_language": "hi",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "hard",
                "domain": "software_engineering",
                "provenance": "Software Engineering Press",
                "split": "calibration",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 81,
                        "text": "సాఫ్ట్‌వేర్ ఇంజనీరింగ్‌లో కోడ్ నాణ్యత మరియు నిరంతర పరీక్షలు చాలా కీలకమైన ప్రక్రియలు.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Cross-lingual Indic translation (Hindi to Telugu)."
            },
            {
                "id": "CALIB-12",
                "suspicious_text": "Unsupervised machine learning methods discover hidden clusters and patterns in raw data without any human labels.",
                "source_text": "Supervised machine learning algorithms require large labeled datasets to achieve high classification accuracy.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "machine_learning",
                "provenance": "Bishop Pattern Recognition",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Shared ML terminology but opposite learning paradigms."
            },
            {
                "id": "CALIB-13",
                "suspicious_text": "Non-relational document databases offer flexible horizontal scalability and eventual consistency across distributed nodes.",
                "source_text": "Relational databases enforce strict ACID transactional consistency using structured schema definitions.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "databases",
                "provenance": "Database Systems Concepts",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Contrasting database paradigms with shared storage vocabulary."
            },
            {
                "id": "CALIB-14",
                "suspicious_text": "The administration strictly prohibited unauthorized software downloads on all workstations without exception.",
                "source_text": "The administration explicitly permitted authorized software downloads on all workstations under supervision.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "policy",
                "provenance": "IT Security Manual",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Hard negative with negation shift ('strictly prohibited' vs 'explicitly permitted')."
            },
            {
                "id": "CALIB-15",
                "suspicious_text": "The census reported 15,200 active industrial facilities in the district during the 2018 fiscal assessment.",
                "source_text": "The census reported 84,900 active commercial entities in the province during the 2024 economic survey.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "economics",
                "provenance": "Statistical Bureau Bulletin",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Hard negative with numerical shift (15,200/2018 vs 84,900/2024)."
            },
            {
                "id": "CALIB-16",
                "suspicious_text": "दक्षिण भारत का तटीय क्षेत्र हिंद महासागर और उष्णकटिबंधीय जलवायु से समृद्ध है।",
                "source_text": "भारत का उत्तरी भाग हिमालय पर्वत श्रृंखलाओं और बर्फीली चोटियों से घिरा हुआ है।",
                "suspicious_language": "hi",
                "source_language": "hi",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "medium",
                "domain": "geography",
                "provenance": "National Geographic Hindi",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Contrasting geographical regions in India."
            },
            {
                "id": "CALIB-17",
                "suspicious_text": "శీతాకాలంలో చల్లని గాలులు మరియు పొగమంచు వాతావరణాన్ని ఆహ్లాదకరంగా మారుస్తాయి.",
                "source_text": "వేసవి కాలంలో తీవ్రమైన ఎండలు మరియు ఉష్ణోగ్రతలు ప్రజలను ఇబ్బందులకు గురిచేస్తాయి.",
                "suspicious_language": "te",
                "source_language": "te",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "medium",
                "domain": "meteorology",
                "provenance": "Eenadu Climate Section",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Contrasting seasonal weather in Telugu."
            },
            {
                "id": "CALIB-18",
                "suspicious_text": "संतुलित शाकाहारी भोजन शरीर को आवश्यक विटामिन, खनिज और पोषक तत्व प्रदान करता है।",
                "source_text": "Cardiovascular exercise strengthens heart muscle contractions and boosts circulatory efficiency.",
                "suspicious_language": "hi",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "health",
                "provenance": "Health and Wellness Digest",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Hard negative cross-lingual: Nutrition vs cardiovascular workout."
            },
            {
                "id": "CALIB-19",
                "suspicious_text": "Artisanal sourdough bread requires precise water temperature, whole grain flour, and overnight fermentation.",
                "source_text": "Convolutional neural networks extract hierarchical spatial representations from raster images.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "unrelated_control",
                "is_plagiarism": False,
                "difficulty": "easy",
                "domain": "culinary",
                "provenance": "Baking Science Handbook",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Unrelated control: Culinary baking vs computer vision."
            },
            {
                "id": "CALIB-20",
                "suspicious_text": "సాంప్రదాయ తెలుగు సాహిత్యంలో నన్నయ, తిక్కన, ఎర్రనలను కవిత్రయంగా గౌరవిస్తారు.",
                "source_text": "सौर ऊर्जा उत्पादन के लिए सिलिकॉन वेफर निर्माण में अत्यधिक शुद्धता की आवश्यकता होती है।",
                "suspicious_language": "te",
                "source_language": "hi",
                "plagiarism_type": "unrelated_control",
                "is_plagiarism": False,
                "difficulty": "easy",
                "domain": "literature",
                "provenance": "Telugu Literary Academy",
                "split": "calibration",
                "ground_truth_spans": [],
                "rationale": "Unrelated control: Classical Telugu poetry vs silicon metallurgy in Hindi."
            },

            # =========================================================================
            # HELD-OUT EVALUATION SPLIT (20 examples: 11 positives, 9 negatives)
            # =========================================================================
            {
                "id": "HELD-01",
                "suspicious_text": "जल संरक्षण के लिए वर्षा जल संचयन प्रणालियों का निर्माण भूजल स्तर को सुधारने में सहायक होता है।",
                "source_text": "जल संरक्षण के लिए वर्षा जल संचयन प्रणालियों का निर्माण भूजल स्तर को सुधारने में सहायक होता है।",
                "suspicious_language": "hi",
                "source_language": "hi",
                "plagiarism_type": "exact",
                "is_plagiarism": True,
                "difficulty": "easy",
                "domain": "hydrology",
                "provenance": "Ministry of Jal Shakti Report (Held-out)",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 105,
                        "text": "जल संरक्षण के लिए वर्षा जल संचयन प्रणालियों का निर्माण भूजल स्तर को सुधारने में सहायक होता है।",
                        "language": "hi",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Held-out exact copy: Hindi water conservation."
            },
            {
                "id": "HELD-02",
                "suspicious_text": "సహజ సిద్ధమైన వ్యవసాయ పద్ధతులు నేల సారాన్ని కాపాడటంలో మరియు సూక్ష్మజీవుల సంఖ్యను పెంచడంలో ఎంతో దోహదపడతాయి.",
                "source_text": "సహజ సిద్ధమైన వ్యవసాయ పద్ధతులు నేల సారాన్ని కాపాడటంలో మరియు సూక్ష్మజీవుల సంఖ్యను పెంచడంలో ఎంతో దోహదపడతాయి.",
                "suspicious_language": "te",
                "source_language": "te",
                "plagiarism_type": "exact",
                "is_plagiarism": True,
                "difficulty": "easy",
                "domain": "agriculture",
                "provenance": "Rythu Bharosa Agricultural Journal (Held-out)",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 107,
                        "text": "సహజ సిద్ధమైన వ్యవసాయ పద్ధతులు నేల సారాన్ని కాపాడటంలో మరియు సూక్ష్మజీవుల సంఖ్యను పెంచడంలో ఎంతో దోహదపడతాయి.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Held-out exact copy: Telugu organic farming."
            },
            {
                "id": "HELD-03",
                "suspicious_text": "Under international intellectual property statutes, creators retain proprietary exclusive rights over their original works for specified periods.",
                "source_text": "Under international intellectual property treaties, authors maintain proprietary exclusive rights over their original creations for defined durations.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "near_exact",
                "is_plagiarism": True,
                "difficulty": "easy",
                "domain": "law",
                "provenance": "WIPO Copyright Treaty Analysis",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 147,
                        "text": "Under international intellectual property statutes, creators retain proprietary exclusive rights over their original works for specified periods.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Near-exact rewrite with minor synonym replacements."
            },
            {
                "id": "HELD-04",
                "suspicious_text": "Distributed consensus protocols guarantee uniform node replication and prevent conflicting transactions across unreliable network partitions.",
                "source_text": "Consensus algorithms in decentralized architectures ensure fault-tolerant state agreement among participating servers despite communication interruptions.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "computer_science",
                "provenance": "Lamport Paxos Consensus Review",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 143,
                        "text": "Distributed consensus protocols guarantee uniform node replication and prevent conflicting transactions across unreliable network partitions.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Complex technical paraphrase in distributed systems."
            },
            {
                "id": "HELD-05",
                "suspicious_text": "नवीकरणीय ऊर्जा स्रोतों को अपनाकर हम कार्बन उत्सर्जन में भारी कमी ला सकते हैं तथा पर्यावरण को स्वच्छ रख सकते हैं।",
                "source_text": "सौर और पवन जैसी स्वच्छ ऊर्जा प्रणालियों के विस्तार से ग्रीनहाउस गैसों का निष्कासन घटता है तथा वायु प्रदूषण नियंत्रित होता है।",
                "suspicious_language": "hi",
                "source_language": "hi",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "environmental_engineering",
                "provenance": "TERI Energy Policy Paper",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 113,
                        "text": "नवीकरणीय ऊर्जा स्रोतों को अपनाकर हम कार्बन उत्सर्जन में भारी कमी ला सकते हैं तथा पर्यावरण को स्वच्छ रख सकते हैं।",
                        "language": "hi",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Hindi renewable energy environmental paraphrase."
            },
            {
                "id": "HELD-06",
                "suspicious_text": "టెలిస్కోపుల ద్వారా ఖగోళ శాస్త్రవేత్తలు విశ్వంలోని సుదూర నక్షత్ర మండలాలు మరియు కృష్ణ బిలాల గమనాన్ని గుర్తిస్తారు.",
                "source_text": "అంతరిక్ష పరిశోధనలలో శక్తివంతమైన దుర్భిణుల సహాయంతో సుదూర గెలాక్సీల నిర్మాణం మరియు బ్లాక్ హోల్స్ గురించి అధ్యయనం చేస్తారు.",
                "suspicious_language": "te",
                "source_language": "te",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "astrophysics",
                "provenance": "ISRO Telugu Space Digest",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 109,
                        "text": "టెలిస్కోపుల ద్వారా ఖగోళ శాస్త్రవేత్తలు విశ్వంలోని సుదూర నక్షత్ర మండలాలు మరియు కృష్ణ బిలాల గమనాన్ని గుర్తిస్తారు.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Telugu astrophysics observation paraphrase."
            },
            {
                "id": "HELD-07",
                "suspicious_text": "The immune system generates specialized antibodies to identify and neutralize pathogenic viruses invading the bloodstream.",
                "source_text": "प्रतिरक्षा प्रणाली रक्तप्रवाह में प्रवेश करने वाले रोगजनक विषाणुओं की पहचान करने और उन्हें निष्क्रिय करने के लिए विशिष्ट एंटीबॉडी बनाती है।",
                "suspicious_language": "en",
                "source_language": "hi",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "immunology",
                "provenance": "Medical Immunology Text",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 124,
                        "text": "The immune system generates specialized antibodies to identify and neutralize pathogenic viruses invading the bloodstream.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Hindi source translated into medical English."
            },
            {
                "id": "HELD-08",
                "suspicious_text": "సముద్రపు ఆటుపోట్ల ఆధారంగా ఉత్పత్తి చేసే టైడల్ ఎనర్జీ నిరంతర విద్యుత్ సరఫరాకు ఎంతో అనుకూలమైన మార్గం.",
                "source_text": "Tidal energy generated from oceanic marine currents offers a highly predictable and continuous clean electricity supply.",
                "suspicious_language": "te",
                "source_language": "en",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "ocean_energy",
                "provenance": "Renewable Marine Energy Monograph",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 99,
                        "text": "సముద్రపు ఆటుపోట్ల ఆధారంగా ఉత్పత్తి చేసే టైడల్ ఎనర్జీ నిరంతర విద్యుత్ సరఫరాకు ఎంతో అనుకూలమైన మార్గం.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "English to Telugu translation in marine engineering."
            },
            {
                "id": "HELD-09",
                "suspicious_text": "ఆప్టికల్ ఫైబర్ కేబుల్స్ కాంతి తరంగాల సంపూర్ణ అంతర్గత పరావర్తనం ద్వారా డేటాను అత్యంత వేగంగా బదిలీ చేస్తాయి.",
                "source_text": "Optical fiber cables transmit high-speed communications through total internal reflection of modulated laser light beams.",
                "suspicious_language": "te",
                "source_language": "en",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "medium",
                "domain": "telecommunications",
                "provenance": "Photonics Principles",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 105,
                        "text": "ఆప్టికల్ ఫైబర్ కేబుల్స్ కాంతి తరంగాల సంపూర్ణ అంతర్గత పరావర్తనం ద్వారా డేటాను అత్యంత వేగంగా బదిలీ చేస్తాయి.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "English to Telugu telecommunications translation."
            },
            {
                "id": "HELD-10",
                "suspicious_text": "రహదారుల నిర్మాణంలో నాణ్యతా ప్రమాణాలు ప్రయాణికుల భద్రతను గణనీయంగా పెంచుతాయి.",
                "source_text": "सड़क निर्माण में उच्च गुणवत्ता के मानक यात्रियों की सुरक्षा सुनिश्चित करने में सहायक सिद्ध होते हैं।",
                "suspicious_language": "te",
                "source_language": "hi",
                "plagiarism_type": "translation",
                "is_plagiarism": True,
                "difficulty": "hard",
                "domain": "civil_engineering",
                "provenance": "NHAI Hindi-Telugu Transport Manual",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 0,
                        "end_char": 73,
                        "text": "రహదారుల నిర్మాణంలో నాణ్యతా ప్రమాణాలు ప్రయాణికుల భద్రతను గణనీయంగా పెంచుతాయి.",
                        "language": "te",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Hindi to Telugu civil engineering translation."
            },
            {
                "id": "HELD-11",
                "suspicious_text": "The committee established that ethical conduct requires transparency. Furthermore, researchers must publicly archive all raw experimental trials without exception.",
                "source_text": "Scientific honesty mandates that scholars make all primary experimental findings and empirical data accessible to the wider academic community.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "paraphrase",
                "is_plagiarism": True,
                "difficulty": "hard",
                "domain": "ethics",
                "provenance": "Academic Integrity Council",
                "split": "held_out_evaluation",
                "ground_truth_spans": [
                    {
                        "start_char": 84,
                        "end_char": 165,
                        "text": "researchers must publicly archive all raw experimental trials without exception.",
                        "language": "en",
                        "label": "plagiarized"
                    }
                ],
                "rationale": "Complex partial paraphrase in research ethics."
            },
            {
                "id": "HELD-12",
                "suspicious_text": "The protocol explicitly prohibited external peripheral connections during secure firmware updates.",
                "source_text": "The protocol explicitly permitted external peripheral connections during secure firmware updates.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "cybersecurity",
                "provenance": "Firmware Protocol Specification",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Single polarity word flip ('prohibited' vs 'permitted')."
            },
            {
                "id": "HELD-13",
                "suspicious_text": "The regional GDP expanded by 8.4% during the third quarter of 2023 due to strong manufacturing outputs.",
                "source_text": "The regional GDP contracted by 2.1% during the third quarter of 2023 due to weak manufacturing outputs.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "economics",
                "provenance": "Federal Reserve Economic Review",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Economic numbers and direction shift (expanded 8.4% vs contracted 2.1%)."
            },
            {
                "id": "HELD-14",
                "suspicious_text": "Reinforcement learning agents optimize sequential actions by maximizing cumulative future rewards through trial and error.",
                "source_text": "Supervised learning classifiers map predefined input features to fixed categorical target labels using cross-entropy loss.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "machine_learning",
                "provenance": "Sutton & Barto Reinforcement Learning",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Hard negative: High shared ML vocabulary but fundamentally different paradigms."
            },
            {
                "id": "HELD-15",
                "suspicious_text": "थार मरुस्थल में अत्यधिक शुष्क जलवायु और रेतीले टीले वनस्पतियों के विकास को गंभीर रूप से सीमित करते हैं।",
                "source_text": "सुंदरबन के मैंग्रोव दलदल में खारे पानी और उच्च आर्द्रता के कारण जैव विविधता अत्यंत समृद्ध है।",
                "suspicious_language": "hi",
                "source_language": "hi",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "medium",
                "domain": "ecology",
                "provenance": "Indian Botanical Survey",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Desert vs mangrove wetland ecosystems in Hindi."
            },
            {
                "id": "HELD-16",
                "suspicious_text": "వైర్‌లెస్ సెల్యులార్ నెట్‌వర్క్‌లు బేస్ స్టేషన్ల ద్వారా మొబైల్ పరికరాలకు రేడియో తరంగాలను ప్రసారం చేస్తాయి.",
                "source_text": "ఆప్టికల్ ఫైబర్ కేబుల్స్ భూగర్భ పైపుల ద్వారా లేజర్ సంకేతాలను ఎక్కువ దూరాలకు చేరవేస్తాయి.",
                "suspicious_language": "te",
                "source_language": "te",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "medium",
                "domain": "telecommunications",
                "provenance": "Telugu Telecom Review",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Hard negative: Wireless radio transmission vs underground fiber optic transmission in Telugu."
            },
            {
                "id": "HELD-17",
                "suspicious_text": "కేంద్ర బ్యాంకు ద్రవ్యోల్బణాన్ని నియంత్రించడానికి వడ్డీ రేట్లను పెంచే విధానాన్ని అవలంబిస్తుంది.",
                "source_text": "Sociological field studies analyze how kinship structures and communal rituals shape family dynamics.",
                "suspicious_language": "te",
                "source_language": "en",
                "plagiarism_type": "hard_negative",
                "is_plagiarism": False,
                "difficulty": "hard",
                "domain": "social_sciences",
                "provenance": "Social Sciences Comparative Review",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Hard negative cross-lingual: Telugu central bank interest rates vs English sociology kinship."
            },
            {
                "id": "HELD-18",
                "suspicious_text": "Decentralized blockchain networks achieve Byzantine fault tolerance through cryptographic proof-of-work protocols.",
                "source_text": "Composting organic vegetable scraps enriches garden soil with beneficial nitrogen and carbon nutrients.",
                "suspicious_language": "en",
                "source_language": "en",
                "plagiarism_type": "unrelated_control",
                "is_plagiarism": False,
                "difficulty": "easy",
                "domain": "cryptography",
                "provenance": "Nakamoto Bitcoin Whitepaper",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Unrelated control: Blockchain cryptography vs organic garden composting."
            },
            {
                "id": "HELD-19",
                "suspicious_text": "Supersonic aerofoils generate shock waves that alter laminar boundary layer airflow at high Mach speeds.",
                "source_text": "महाकवि कालिदास द्वारा रचित मेघदूतम् संस्कृत साहित्य की एक अद्वितीय और अमर काव्य रचना है।",
                "suspicious_language": "en",
                "source_language": "hi",
                "plagiarism_type": "unrelated_control",
                "is_plagiarism": False,
                "difficulty": "easy",
                "domain": "aerospace",
                "provenance": "Aeronautical Engineering Review",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Unrelated control: Supersonic aerodynamics vs classical Sanskrit poetry."
            },
            {
                "id": "HELD-20",
                "suspicious_text": "Relational third normal form eliminates transitive functional dependencies in database table schemas.",
                "source_text": "కూచిపూడి నృత్యం ఆంధ్రప్రదేశ్ సంస్కృతికి అద్దం పట్టే ప్రాచీన మరియు ప్రసిద్ధ శాస్త్రీయ నృత్య రూపం.",
                "suspicious_language": "en",
                "source_language": "te",
                "plagiarism_type": "unrelated_control",
                "is_plagiarism": False,
                "difficulty": "easy",
                "domain": "databases",
                "provenance": "Database Theory",
                "split": "held_out_evaluation",
                "ground_truth_spans": [],
                "rationale": "Unrelated control: Database normalization in English vs Kuchipudi classical dance in Telugu."
            }
        ]
    }

    # Programmatically calculate start_char and end_char for any span with text
    for ex in data["examples"]:
        for span in ex["ground_truth_spans"]:
            txt = span["text"]
            idx = ex["suspicious_text"].find(txt)
            if idx == -1:
                raise ValueError(f"Span text '{txt}' not found in suspicious text '{ex['suspicious_text']}'")
            span["start_char"] = idx
            span["end_char"] = idx + len(txt)

    out_file = Path("data/evaluation/benchmark_dataset_v1.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Wrote benchmark dataset to {out_file}. Validating...")
    ds = load_benchmark_dataset(out_file)
    print(f"Successfully loaded and validated {len(ds.examples)} examples across {ds.languages}.")

if __name__ == "__main__":
    build_dataset()
