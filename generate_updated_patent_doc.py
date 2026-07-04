from copy import deepcopy
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

prior_paras = [
    'Prior Art',
    'Several patient monitoring and clinical alert management systems have been proposed using wearable sensors and remote monitoring technologies.',
    'For example, US9195799B2 describes a remote patient monitoring system capable of collecting physiological parameters and transmitting the data to a monitoring platform for medical observation. Although the system supports remote health monitoring, such disclosure primarily emphasizes physiological acquisition and communication and does not teach context-aware alert prioritization using stored patient metadata in combination with caregiver-context conditions.',
    'US9213956B2 discloses a system for monitoring patient physiological signals and notifying healthcare personnel when abnormal conditions are detected. While such systems provide continuous monitoring capability, they do not disclose adaptive alert routing based on caregiver proximity or caregiver-context state for reducing unnecessary escalation and alarm burden.',
    'EP3806104A1 presents a medical monitoring framework for processing patient data and generating alerts using automated analysis. However, such disclosure does not teach differentiated alert escalation strategies based on hospital ward classification, including distinct handling for general wards and critical care environments.',
    'CN113558585A discloses an intelligent medical condition monitoring and early warning system that utilizes physiological sensor data and analytical models to detect abnormal patient conditions. While the system improves automated detection of patient deterioration, it does not disclose determining alert priority using patient-specific contextual information including disease condition, medication status, allergy information, and age-related risk factors in a unified caregiver-notification workflow.',
    'Accordingly, known monitoring systems largely focus on physiological signal acquisition, automated warning generation, or generic healthcare notification. They do not teach an integrated architecture that combines wearable sensing, stored patient metadata, ward-specific escalation logic, and caregiver proximity-aware notification in a unified adaptive clinical alert management system.',
    'There therefore remains a need for a monitoring system capable of adaptive clinical alert prioritization and context-aware caregiver notification that improves response efficiency and reduces alarm fatigue in hospital environments.'
]

claim_paras = [
    'Claims',
    '1. A patient monitoring and clinical alert management system comprising: a wearable monitoring device associated with an identified patient and configured to provide physiological data; a data-processing server in communication with the wearable monitoring device; a patient database configured to store patient-specific contextual information including at least one of disease condition, medication information, allergy information, age information, body-condition information, genetic-condition information, and ward classification; a prioritization engine executed by the data-processing server and configured to determine an alert priority based on a combination of the physiological data and the patient-specific contextual information; a ward-management module configured to apply different alert-handling rules according to whether the identified patient is assigned to a general ward or a critical ward; and a caregiver notification module configured to transmit an alert to at least one caregiver device according to the determined alert priority and a caregiver-context condition.',
    '2. The system as claimed in claim 1, wherein alert generation and escalation are not based solely on predefined physiological threshold crossing.',
    '3. The system as claimed in claim 1, wherein the caregiver-context condition includes at least one of caregiver proximity, caregiver availability, caregiver acknowledgement state, or caregiver role.',
    '4. The system as claimed in claim 1, wherein the prioritization engine is configured to assign different alert priorities to substantially similar physiological readings for different patients based on differences in the patient-specific contextual information.',
    '5. The system as claimed in claim 1, wherein the ward-management module applies a first escalation policy for a general ward patient and a second escalation policy, different from the first escalation policy, for a critical ward patient.',
    '6. The system as claimed in claim 1, wherein the caregiver notification module is configured to modify an alert mode according to caregiver proximity, including issuing a lower-intensity notification when a caregiver is within a predefined distance of the patient and issuing a higher-intensity notification when the caregiver is beyond the predefined distance.',
    '7. The system as claimed in claim 1, wherein the system further comprises a mobile caregiver application configured to receive alerts, display patient status information, and transmit an acknowledgement or attendance response to the data-processing server.',
    '8. The system as claimed in claim 1, wherein the physiological data includes at least heart rate, oxygen saturation, and body temperature.',
    '9. The system as claimed in claim 1, wherein the system is operable in a hardware mode using live physiological sensor readings and in a simulation mode using generated or controlled physiological data.',
    '10. The system as claimed in claim 1, wherein the prioritization engine computes an early warning score and combines the early warning score with the patient-specific contextual information to determine the alert priority.',
    '11. The system as claimed in claim 1, further comprising a wearable-assignment control module configured to associate the wearable monitoring device with the identified patient at admission and to release the wearable monitoring device upon discharge.',
    '12. The system as claimed in claim 1, wherein the caregiver notification module is configured to reduce alarm fatigue by suppressing, delaying, downgrading, or rerouting selected alerts based on the determined alert priority and the caregiver-context condition.',
    '13. A method for patient monitoring and clinical alert management comprising: receiving physiological data from a wearable monitoring device associated with a patient; retrieving patient-specific contextual information stored for the patient; determining an alert priority based on a combination of the physiological data and the patient-specific contextual information; selecting an escalation policy according to a ward classification assigned to the patient; determining a caregiver notification action based on the alert priority and a caregiver-context condition; and transmitting an alert to a caregiver device according to the caregiver notification action.',
    '14. The method as claimed in claim 13, wherein the patient-specific contextual information includes at least one of disease condition, medication information, allergy information, age information, body-condition information, genetic-condition information, or ward classification, and wherein the caregiver notification action is not determined solely by fixed physiological threshold crossing.'
]


def para_text(paragraph):
    return ''.join(t.text or '' for t in paragraph.findall('.//w:t', NS)).strip()


def set_para_text(paragraph, text):
    texts = paragraph.findall('.//w:t', NS)
    if texts:
        texts[0].text = text
        for t in texts[1:]:
            t.text = ''
    else:
        run = ET.SubElement(paragraph, W + 'r')
        node = ET.SubElement(run, W + 't')
        node.text = text


def update_doc(source_path: Path, target_path: Path):
    with zipfile.ZipFile(source_path, 'r') as zin:
        xml = zin.read('word/document.xml')
        members = [(name, zin.read(name)) for name in zin.namelist() if name != 'word/document.xml']

    tree = ET.fromstring(xml)
    body = tree.find('w:body', NS)
    paragraphs = body.findall('w:p', NS)
    texts = [para_text(p) for p in paragraphs]

    prior_idx = texts.index('Prior Art')
    claims_idx = texts.index('Claims')
    abstract_idx = texts.index('Abstract')

    prior_heading_template = deepcopy(paragraphs[prior_idx])
    prior_body_template = deepcopy(paragraphs[prior_idx + 1])
    claims_heading_template = deepcopy(paragraphs[claims_idx])
    claims_body_template = deepcopy(paragraphs[claims_idx + 1])

    new_prior = []
    for index, text in enumerate(prior_paras):
        paragraph = deepcopy(prior_heading_template if index == 0 else prior_body_template)
        set_para_text(paragraph, text)
        new_prior.append(paragraph)

    new_claims = []
    for index, text in enumerate(claim_paras):
        paragraph = deepcopy(claims_heading_template if index == 0 else claims_body_template)
        set_para_text(paragraph, text)
        new_claims.append(paragraph)

    current = body.findall('w:p', NS)
    for paragraph in current[prior_idx:claims_idx]:
        body.remove(paragraph)
    for paragraph in reversed(new_prior):
        body.insert(prior_idx, paragraph)

    current = body.findall('w:p', NS)
    texts = [para_text(p) for p in current]
    claims_idx = texts.index('Claims')
    abstract_idx = texts.index('Abstract')
    for paragraph in current[claims_idx:abstract_idx]:
        body.remove(paragraph)
    for paragraph in reversed(new_claims):
        body.insert(claims_idx, paragraph)

    new_xml = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
    with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for name, data in members:
            zout.writestr(name, data)
        zout.writestr('word/document.xml', new_xml)


source = Path(r'C:\Users\Lenovo\Documents\Form 2_Copy_No_Edits.docx')
target = Path(r'C:\Users\Lenovo\Documents\Form 2_PriorArt_Claims_Updated.docx')
update_doc(source, target)
print(target)
