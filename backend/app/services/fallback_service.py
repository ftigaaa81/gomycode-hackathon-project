"""Safe defaults and curated demo responses for jury rehearsals."""

from __future__ import annotations

import random
from typing import TypedDict

from app.schemas.analysis import (
    AnalysisLanguage,
    AnalysisSource,
    AnalyzeResponse,
    UrgenceLevel,
)


class _DemoTemplate(TypedDict):
    urgence: UrgenceLevel
    message_court: str
    objet_principal: str
    texte_detecte: str | None


class _LocalizedDemoTemplate(TypedDict):
    en: _DemoTemplate
    ar: _DemoTemplate


DEMO_RESPONSES: dict[str, _LocalizedDemoTemplate] = {
    "escalier_danger": {
        "en": {
            "urgence": UrgenceLevel.DANGER,
            "message_court": "Escalier devant vous, arrêtez-vous.",
            "objet_principal": "escalier",
            "texte_detecte": None,
        },
        "ar": {
            "urgence": UrgenceLevel.DANGER,
            "message_court": "درج أمامك، توقف.",
            "objet_principal": "درج",
            "texte_detecte": None,
        },
    },
    "panneau_texte": {
        "en": {
            "urgence": UrgenceLevel.ATTENTION,
            "message_court": "Panneau sortie à droite.",
            "objet_principal": "panneau",
            "texte_detecte": "SORTIE",
        },
        "ar": {
            "urgence": UrgenceLevel.ATTENTION,
            "message_court": "لافتة خروج على اليمين.",
            "objet_principal": "لافتة",
            "texte_detecte": "خروج",
        },
    },
    "rue_calme": {
        "en": {
            "urgence": UrgenceLevel.NORMAL,
            "message_court": "Rue calme, peu de passage.",
            "objet_principal": "rue",
            "texte_detecte": None,
        },
        "ar": {
            "urgence": UrgenceLevel.NORMAL,
            "message_court": "الشارع هادئ وحركة المرور قليلة.",
            "objet_principal": "شارع",
            "texte_detecte": None,
        },
    },
    "obstacle_bas": {
        "en": {
            "urgence": UrgenceLevel.ATTENTION,
            "message_court": "Obstacle bas, marche haute.",
            "objet_principal": "obstacle",
            "texte_detecte": None,
        },
        "ar": {
            "urgence": UrgenceLevel.ATTENTION,
            "message_court": "عائق منخفض ودرجة مرتفعة.",
            "objet_principal": "عائق",
            "texte_detecte": None,
        },
    },
    "vehicule_proche": {
        "en": {
            "urgence": UrgenceLevel.DANGER,
            "message_court": "Véhicule proche, reculez.",
            "objet_principal": "véhicule",
            "texte_detecte": None,
        },
        "ar": {
            "urgence": UrgenceLevel.DANGER,
            "message_court": "مركبة قريبة، تراجع.",
            "objet_principal": "مركبة",
            "texte_detecte": None,
        },
    },
}

_DEMO_SCENE_IDS = tuple(DEMO_RESPONSES.keys())


def build_fallback_response(
    source: AnalysisSource,
    langue: AnalysisLanguage = "en",
) -> AnalyzeResponse:
    """
    Return a conservative analysis so the user never receives a raw server error.

    Messages are generic and avoid inventing scene details.
    """
    return AnalyzeResponse(
        urgence=UrgenceLevel.ATTENTION,
        message_court=(
            "التحليل غير متاح، يرجى توخي الحذر."
            if langue == "ar"
            else "Analyse indisponible, restez prudent."
        ),
        objet_principal="غير معروف" if langue == "ar" else "inconnu",
        texte_detecte=None,
        source=source,
        used_fallback=True,
    )


def get_demo_response(
    scene_id: str,
    *,
    source: AnalysisSource = AnalysisSource.MOBILE,
    langue: AnalysisLanguage = "en",
) -> AnalyzeResponse:
    """Return a curated demo scene as a typed AnalyzeResponse."""
    resolved_id = scene_id
    if scene_id == "random":
        resolved_id = random.choice(_DEMO_SCENE_IDS)

    localized_templates = DEMO_RESPONSES.get(resolved_id)
    if localized_templates is None:
        raise KeyError(resolved_id)
    template = localized_templates[langue]

    return AnalyzeResponse(
        urgence=template["urgence"],
        message_court=template["message_court"],
        objet_principal=template["objet_principal"],
        texte_detecte=template["texte_detecte"],
        source=source,
        used_fallback=False,
    )
