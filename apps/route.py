import os

IS_TEST = True if os.environ.get("IS_TEST", 'False').lower() =='false' else True

def route(data_service):

    evidence_type = 'test' if IS_TEST else data_service.evidenceTypeClassification
    match evidence_type:
        case "https://sr.oots.tech.ec.europa.eu/evidencetypeclassifications/MT/a6016402-8190-409f-9ff2-eac34b1dbbd8":
            from getEvidences.GetDiplomaSupplement import Evidence, EvidenceMetadata
            return Evidence(), EvidenceMetadata(), True
        case _:
            from .EvidanceTEST import Evidance
            return Evidance(), None, False
