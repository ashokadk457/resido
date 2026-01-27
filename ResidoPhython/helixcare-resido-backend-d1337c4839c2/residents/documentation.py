class PatientChartsExportAPIDocumentation:
    OPERATION_ID = "Helixbeat EHI Export Request Workflow"
    OPERATION_DESCRIPTION = """
    # Helixbeat EHI Export Workflow

    The patient (single or multiple) data export functionality is designed to allow healthcare providers to export EHI for multiple residousers simultaneously, which is particularly useful for data migrations or population health analysis.
    The workflow includes:

    1. **Request Initiation** : The provider initiates the bulk export request through the Helixbeat platform or
        API, selecting the group of residents.
    2. **Authorization** : The system verifies the provider’s authorization for accessing and exporting multiple
        patient records.
    3. **Processing** : The system retrieves the EHI for all residousers included in the request, ensuring complete
        data export.
    4. **Export** : Data is exported in **FHIR Bulk Data (NDJSON)** or **CCDA** format, optimized for large-scale
        data exports.
    5. **Completion and Notification** : The provider is notified upon successful completion of the export,
        and the transaction is recorded in the audit trail.

    # Data Formats

    Helixbeat supports multiple standardized formats for exporting EHI to ensure interoperability and
    compliance:

    - **FHIR R4 (JSON/XML)** : Exported data is structured in accordance with FHIR R4 standards, which are
        widely used across healthcare systems for representing clinical data in a structured format.
    - **CCDA (Consolidated Clinical Document Architecture)** : he CCDA format can be used for
        compatibility with other health IT systems. **CCDA** can be exported in the following formats:

    ```
    o XML : A structured, machine-readable format for integration with other health IT systems.
    ```
    ```
    o HTML : A human-readable format that can be easily viewed in web browsers or other
    applications.
    ```
    ```
    o PDF : A document format suitable for printing or sharing human-readable clinical summaries
    in a secure, unalterable form.
    ```
    - **FHIR Bulk Data (NDJSON)** : For multiple patient exports, data is exported in **NDJSON** format, which is
        designed for handling large datasets and supports efficient batch processing.
    """


class PatientChartsExportRequestProcessAPIDocumentation:
    OPERATION_ID = "Helixbeat EHI Export Request Process Workflow"
    OPERATION_DESCRIPTION = """
# Data Elements

Helixbeat ensures that all necessary data elements required under §170.315(b)(10) are included in the
exported files. The EHI export includes:


## Patient Demographics

- Name
- Date of Birth
- Gender
- Contact Information

## Clinical Information

- Clinical Notes
- Allergies and Intolerances
- Medications (current and past)
- Immunizations
- Lab and Diagnostic Test Results
- Procedures and Treatments
- Vital Signs

## Encounter Data

- Admission and Discharge Summaries
- Encounter Type (Inpatient, Outpatient, Emergency)
- Provider Information

## Administrative Data

- Insurance Information
- Billing and Claims Data
- Social Determinants of Health (Housing, Employment, etc.)
"""
