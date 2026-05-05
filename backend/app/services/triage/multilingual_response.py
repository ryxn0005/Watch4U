"""Localized response templates for staged triage."""

SUPPORTED_LANGUAGES = {"en", "vi"}
DEFAULT_LANGUAGE = "en"

TEMPLATES = {
    "en": {
        "monitoring": "A fall has been detected. I am checking on you now. Please stay still if you are hurt.",
        "patient_check": "Are you okay? Please say 'I am okay' if you do not need help, or say 'help' if you need assistance.",
        "patient_recheck": "Thank you. I will keep monitoring for a short time. Please call for help if pain or dizziness starts.",
        "carer_alert": "Watch4U detected a fall and recommends checking on the patient now.",
        "emergency_escalation": "There has been no response after the fall. Watch4U is escalating this urgently to the emergency contact.",
        "critical_escalation": "Emergency warning signs were detected after a fall. Watch4U recommends immediate emergency assistance.",
        "false_alarm_cancelled": "Thank you for confirming you are okay. The fall alert has been cancelled.",
    },
    "vi": {
        "monitoring": "Hệ thống phát hiện có thể bạn bị té. Tôi đang kiểm tra bạn. Nếu bị đau, xin hãy nằm yên.",
        "patient_check": "Bạn có ổn không? Nếu không cần giúp, xin nói 'tôi ổn'. Nếu cần giúp, xin nói 'cứu tôi'.",
        "patient_recheck": "Cảm ơn bạn. Tôi sẽ theo dõi thêm một lúc. Nếu thấy đau hoặc chóng mặt, xin gọi giúp đỡ.",
        "carer_alert": "Watch4U phát hiện một cú té và khuyên người chăm sóc kiểm tra người bệnh ngay.",
        "emergency_escalation": "Sau cú té vẫn chưa có phản hồi. Watch4U đang báo khẩn cho người liên hệ cấp cứu.",
        "critical_escalation": "Có dấu hiệu nguy hiểm sau cú té. Watch4U khuyên cần hỗ trợ cấp cứu ngay.",
        "false_alarm_cancelled": "Cảm ơn bạn đã xác nhận là bạn ổn. Cảnh báo té đã được hủy.",
    },
}


def normalize_language(language: str | None) -> str:
    """Return a supported language code, falling back to English."""
    if not language:
        return DEFAULT_LANGUAGE

    language_code = language.lower().split("-", maxsplit=1)[0]
    if language_code in SUPPORTED_LANGUAGES:
        return language_code
    return DEFAULT_LANGUAGE


def get_message(stage: str, language: str | None = DEFAULT_LANGUAGE) -> tuple[str, str]:
    """Return message text and the normalized language used."""
    normalized_language = normalize_language(language)
    template = TEMPLATES[normalized_language].get(stage)

    if template is None:
        template = TEMPLATES[DEFAULT_LANGUAGE][stage]
        normalized_language = DEFAULT_LANGUAGE

    return template, normalized_language
