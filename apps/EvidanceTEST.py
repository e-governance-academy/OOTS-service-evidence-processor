import logging
import pathlib
import uuid

from lxml import etree

from utils.EDMRequestParsing import EDMRequestParsing
from utils.EvidanceABC import (
    EMetadata,
    IssuingAuthority,
    IsAbout,
    IsConformantTo,
    Distribution,
)
from utils.NS import NS

_logger = logging.getLogger(__name__)

path = pathlib.Path(__file__).parent


def metadata(person):
    distribution = Distribution("application/xml")
    conformantTo = IsConformantTo(
        "https://sr.oots.tech.ec.europa.eu/requirements/5247bb6b-6bec-43fd-9b2e-f99be2dbae39"
    )
    usingAuthority = IssuingAuthority(
        "urn:cef.eu:names:identifier:EAS:9930", "DE7657587001"
    )
    usingAuthority.name(lang="UA", name="Міністерство зароботку")
    about = IsAbout(person)

    metadata = EMetadata()
    metadata.isAbout(about.xml)
    metadata.isConformeant(conformantTo.xml)
    metadata.distribution(distribution.xml)
    metadata.issuingAuthority(usingAuthority.xml)
    return metadata.xml_string


class Evidance(NS):
    def __init__(self):
        self._evidence = {
            "title": "Тестовий доказ",
            "PreviewDescription": [
                {"UA": "Обери свій диплом"},
                {"EN": "Please select your diploma."},
            ],
            "preview": True,
            "evidences": [],
        }
        self._request = None

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, request: EDMRequestParsing):
        self._request = request

    @property
    def evidence(self):
        return self._evidence

    @property
    def naturale_person(self):
        person = etree.Element(self._tname("sdg", "NaturalPerson"), nsmap=self._ns)
        person[:] = self.request.natural_person[:]
        return person

    def get_evidence(self, request: EDMRequestParsing):
        self.request = request

        files = [
            path.parent / "EvidenceExamles" / "secondaryEducationEvidence(1).xml",
            path.parent / "EvidenceExamles" / "secondaryEducationEvidence(2).xml",
        ]

        xmls = [etree.parse(file.as_posix()) for file in files]

        for xml in xmls:
            evidence_metadata = metadata(self.naturale_person)
            self._evidence["evidences"].append(
                {
                    "cid": f"cid:{uuid.uuid4()}@gov.ua",
                    "content_type": "application/xml",
                    "content": etree.tostring(xml, encoding="utf8").decode("utf8"),
                    "permit": False,
                    "metadata": evidence_metadata,
                }
            )
            _logger.debug(f"Metadata: {evidence_metadata}")

    @property
    def to_redis(self):
        return self.evidence
