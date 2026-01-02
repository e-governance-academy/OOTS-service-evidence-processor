import logging

from lxml import etree

_logger = logging.getLogger(__name__)


class EDMRequestParsing:
    def __init__(self, request: str):
        self.request = etree.fromstring(request)
        self._ns = {}
        for perfix, uri in self.request.nsmap.items():
            if perfix is None:
                perfix = "default"
            self._ns.update({perfix: uri})
        self.query = self.request.find(".//query:Query", namespaces=self._ns)

    def _slot(self, name):
        slot = self.request.find(f".//rim:Slot[@name='{name}']", namespaces=self._ns)
        if slot is None:
            return False
        return slot

    @property
    def request_id(self):
        return self.request.attrib.get("id")

    @property
    def is_possibility_for_preview(self):
        slot = self._slot("PossibilityForPreview")
        if slot:
            value = slot.find(".//rim:Value", namespaces=self._ns)
            if value is not None:
                return True if "true".lower() == value.text.lower() else False
        return False

    @property
    def is_second(self) -> bool:
        pl = self.preview_location
        _logger.debug(f"is_second: {pl}")
        if pl is None or not pl:
            return False
        return True

    @property
    def preview_location(self) -> str | None:
        pl = self.slot_text("PreviewLocation")
        _logger.debug(f"preview_location: {pl}")
        return pl

    def requirments(self) -> list[etree._Element] | None:
        slot = self._slot("Requirements")
        if slot is None:
            return None
        requirement = slot.findall(".//sdg:Requirement", namespaces=self._ns)
        return requirement

    def requester(self) -> list[etree._Element] | None:
        slot = self._slot("EvidenceRequester")
        if slot is None:
            return None
        value = slot.findall(".//sdg:Agent", namespaces=self._ns)
        return value

    def provider(self) -> list[etree._Element] | None:
        slot = self._slot("EvidenceProvider")
        if slot is None:
            return None
        value = slot.findall(".//sdg:Agent", namespaces=self._ns)
        return value

    def evidence_request(self):
        slot = self._slot("EvidenceRequest")
        if slot is None:
            return False
        value = slot.find(".//sdg:DataServiceEvidenceType", namespaces=self._ns)
        return value

    @property
    def evidenceTypeClassification(self) -> str | None:
        if self.query is None:
            return None
        classification = self.query.find(
            ".//sdg:EvidenceTypeClassification", namespaces=self._ns
        )
        if classification is None:
            return None
        return classification.text

    @property
    def natural_person(self) -> etree._Element | None:
        slot = self._slot("NaturalPerson")
        if slot is None:
            return None
        person = slot.find(".//sdg:Person", namespaces=self._ns)
        return person

    def slot_text(self, name):
        slot = self._slot(name)
        if not slot:
            return None
        value = slot.find(".//rim:Value", namespaces=self._ns)
        return value.text

    def all_slots(self, query: bool = False) -> dict[str, str | etree._Element | None]:
        if isinstance(self.query, etree._Element):
            slots = self.query.findall(".//rim:Slot", namespaces=self._ns)
        else:
            slots = self.request.findall(".//rim:Slot", namespaces=self._ns)
        result: dict[str, str | etree._Element | None] = {}
        for slot in slots:
            name = slot.get("name")
            if not name:
                continue
            value = slot.find(".//rim:Value", namespaces=self._ns)
            if name and value is not None:
                result[name] = value.text
            if not value:
                value = slot.find(".//rim:SlotValue", namespaces=self._ns)
            if value is not None:
                for chaild in value.iterchildren():
                    if isinstance(chaild, etree._Element | str):
                        result[name] = chaild
        return result
