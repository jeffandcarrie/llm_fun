from functools import lru_cache

from agent_framework import tool
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine


@lru_cache(maxsize=1)
def _engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    ).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
    return analyzer, AnonymizerEngine()


@tool
def anonymize_text(text: str, entities: list[str] | None = None) -> str:
    """Anonymize detected personally identifiable information in English text."""
    if not text.strip():
        return text

    try:
        analyzer, anonymizer = _engines()
    except OSError:
        return (
            "PII anonymization is not configured. Install the English spaCy model with "
            "`uv run python -m spacy download en_core_web_sm` and try again."
        )

    results = analyzer.analyze(text=text, entities=entities, language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text