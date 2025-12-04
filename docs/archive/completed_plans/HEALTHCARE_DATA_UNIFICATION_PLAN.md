# 🏥 Healthcare Data Unification Plan

## Domain-Customizable Linguistic Knowledge Web for Legacy System Integration

---

## Executive Summary

The Butterfly/Convergence Engine can be customized to function as an **intelligent data harmonization layer** that learns to map between disparate healthcare database architectures. Organisms evolve to discover consistent (VP-validated) translations between legacy and modern systems.

**Key Insight**: The system doesn't need to "understand" healthcare - it needs to learn that when `ADT_A01` appears in System A, it consistently maps to `Encounter.create` in System B. The VP (Violation Pressure) system validates these mappings are *lawful* (consistent, reversible, stable).

---

## Phase 0: Stabilize Current System (PREREQUISITE)

> ⚠️ **CRITICAL**: Complete these before domain customization!

### 0.1 Current Issues to Resolve

| Issue | Status | File(s) |
|-------|--------|---------|
| Neural `load_state_dict` size mismatch | ✅ Fixed | `neural_organism.py`, `trainer.py`, `brain.py`, `organism_capsule.py`, `ray_tasks.py` |
| Explorer panel showing 0s | ✅ Fixed | `unified_entry.py` (wired controller components to PhaseSyncBridge) |
| NeuralTrainer AttributeError | 🔍 Monitor | Need full error message if it recurs |
| Trainer organisms iteration bug | ✅ Fixed | `trainer.py` (`.values()` fix) |

### 0.2 Validation Checklist

Before proceeding to Phase 1, verify:

- [ ] System runs without errors for 100+ generations
- [ ] Explorer panel shows non-zero values (Sovereigns, Stability, Genesis%)
- [ ] Neural panel shows "ACTIVE" not "ERROR"
- [ ] Highlander battles execute successfully
- [ ] VP calculations accumulate over time
- [ ] Language model training occurs (check `avg_language_loss` in logs)
- [ ] Web UI accessible at `localhost:5000`

### 0.3 Baseline Metrics to Capture

Run the current system and document:
```
- Organisms per generation: ___
- VP convergence rate: ___
- Highlander winner survival rate: ___
- Language loss convergence: ___
- Time to 500 organisms: ___
```

---

## Phase 1: Domain Vocabulary Foundation

### 1.1 Create Healthcare Vocabulary Seed File

**File**: `data/healthcare_vocabulary_50k.json`

```json
{
  "source": "healthcare_domain_curated",
  "version": "1.0.0",
  "total_words": 50000,
  "domain": "healthcare_data_integration",
  "categories": {
    "clinical_concepts": 8000,
    "data_structures": 5000,
    "legacy_system_terms": 7000,
    "modern_standards": 5000,
    "integration_verbs": 3000,
    "temporal_concepts": 2000,
    "quality_indicators": 2000,
    "general_english": 18000
  },
  "words": []
}
```

### 1.2 Category Definitions

#### Clinical Concepts (~8,000 terms)
```
patient, encounter, diagnosis, procedure, medication, allergy,
vital_sign, lab_result, observation, condition, care_plan,
immunization, family_history, social_history, chief_complaint,
assessment, plan, progress_note, discharge_summary, referral,
order, prescription, administration, dosage, frequency, route,
ICD10_A00, ICD10_A01, ..., CPT_99213, CPT_99214, ...,
SNOMED_12345678, LOINC_12345-6, RxNorm_12345, NDC_12345678901
```

#### Legacy System Terms (~7,000 terms)
```
# HL7 v2.x
ADT_A01, ADT_A02, ADT_A03, ADT_A04, ADT_A08, ORM_O01, ORU_R01,
MSH_segment, PID_segment, PV1_segment, OBR_segment, OBX_segment,
field_separator, component_separator, repetition_separator,
encoding_characters, message_control_id, processing_id,

# Mainframe/COBOL
COBOL_copybook, fixed_width_record, packed_decimal, COMP3,
EBCDIC_encoding, record_layout, PIC_clause, REDEFINES,
sequential_file, VSAM_dataset, JCL_job, batch_process,

# Legacy Databases
MUMPS_global, FileMan_record, RPMS_file, VistA_routine,
hierarchical_db, network_db, IDMS_record, IMS_segment,
flat_file, delimited_record, CSV_row, fixed_position
```

#### Modern Standards (~5,000 terms)
```
# FHIR R4
FHIR_Patient, FHIR_Encounter, FHIR_Observation, FHIR_Condition,
FHIR_Procedure, FHIR_MedicationRequest, FHIR_DiagnosticReport,
FHIR_Bundle, FHIR_Reference, FHIR_Extension, FHIR_CodeableConcept,
RESTful_API, JSON_resource, XML_resource, SMART_on_FHIR,

# CDA/CCDA
CDA_document, CCDA_section, CCD_template, structured_body,
clinical_statement, entry_relationship, observation_media,

# Modern Integration
API_endpoint, webhook, event_stream, message_queue,
Kafka_topic, RabbitMQ_exchange, Azure_ServiceBus,
ETL_pipeline, data_lake, data_warehouse, CDC_stream
```

#### Integration Verbs (~3,000 terms)
```
# Transformation
transform, translate, map, convert, normalize, standardize,
parse, serialize, deserialize, encode, decode, validate,

# Data Operations  
merge, deduplicate, reconcile, match, link, resolve,
enrich, augment, cleanse, filter, aggregate, pivot,

# Quality
validate, verify, conform, certify, audit, trace,
version, snapshot, checkpoint, rollback, recover
```

### 1.3 Config.json Updates

```json
{
  "neural": {
    "language_model": {
      "enabled": true,
      "vocabulary": {
        "max_size": 50000,
        "seed_file": "data/healthcare_vocabulary_50k.json",
        "special_tokens": [
          "<PAD>", "<UNK>", "<START>", "<END>", "<VP_GATE>",
          "<LEGACY>", "<MODERN>", "<MAPS_TO>", "<INVALID>"
        ],
        "domain": "healthcare_data_integration"
      }
    }
  }
}
```

---

## Phase 2: Semantic Relation Customization

### 2.1 Healthcare-Specific Relations

Add to `linguistic_knowledge_web.py`:

```python
HEALTHCARE_RELATIONS = {
    # Standard Mappings (bidirectional, low VP expected)
    ('ADT_A01', 'maps_to', 'FHIR_Encounter_create'),
    ('ADT_A03', 'maps_to', 'FHIR_Encounter_discharge'),
    ('ORM_O01', 'maps_to', 'FHIR_ServiceRequest'),
    ('ORU_R01', 'maps_to', 'FHIR_DiagnosticReport'),
    
    # Code System Translations
    ('ICD9_diagnosis', 'superseded_by', 'ICD10_diagnosis'),
    ('CPT_procedure', 'equivalent_to', 'SNOMED_procedure'),
    ('NDC_medication', 'maps_to', 'RxNorm_medication'),
    
    # Architecture Evolution
    ('MUMPS_global', 'modernizes_to', 'relational_table'),
    ('flat_file', 'transforms_to', 'JSON_resource'),
    ('batch_process', 'evolves_to', 'event_stream'),
    ('fixed_width', 'parses_to', 'structured_object'),
    
    # Data Quality Relations
    ('validated', 'enables', 'trusted'),
    ('duplicated', 'requires', 'reconciliation'),
    ('orphaned', 'blocks', 'integration'),
    ('matched', 'produces', 'linked_record')
}
```

### 2.2 Organism-Behavior Mappings

```python
HEALTHCARE_STATE_WORD_MAP = {
    # Organism states map to integration states
    'high_energy': ['processing', 'transforming', 'validating'],
    'low_energy': ['queued', 'pending', 'backlogged'],
    'connected': ['integrated', 'linked', 'synchronized'],
    'isolated': ['orphaned', 'unmatched', 'siloed'],
    'growing': ['enriching', 'augmenting', 'expanding'],
    'declining': ['deprecated', 'retiring', 'archiving']
}

HEALTHCARE_ACTION_WORD_MAP = {
    0: ['move', 'route', 'transfer', 'migrate'],      # MOVE action
    1: ['connect', 'link', 'integrate', 'bind'],      # CONNECT action
    2: ['disconnect', 'unlink', 'isolate', 'sever'],  # DISCONNECT action
    3: ['share', 'publish', 'broadcast', 'emit'],     # SHARE action
    4: ['consume', 'ingest', 'absorb', 'parse'],      # CONSUME action
    5: ['rest', 'queue', 'buffer', 'hold']            # REST action
}
```

---

## Phase 3: VP-Based Validation Rules

### 3.1 Mapping Consistency as VP

The VP system naturally validates data mappings:

| Scenario | VP Level | Meaning |
|----------|----------|---------|
| A→B and B→A consistent | VP0 (0.0-0.25) | Lawful bidirectional mapping |
| A→B works, B→A loses data | VP1 (0.25-0.5) | Lossy transformation (acceptable) |
| A→B inconsistent across records | VP2 (0.5-0.75) | Unstable mapping (needs review) |
| A→B produces errors | VP3 (0.75-1.0) | Invalid mapping (reject) |

### 3.2 Custom VP Traits for Healthcare

```python
HEALTHCARE_VP_TRAITS = {
    'referential_integrity': {
        'description': 'Foreign key relationships preserved',
        'weight': 0.2,
        'validator': check_referential_integrity
    },
    'code_validity': {
        'description': 'All codes exist in target code system',
        'weight': 0.15,
        'validator': check_code_validity
    },
    'temporal_consistency': {
        'description': 'Dates/times remain logically ordered',
        'weight': 0.15,
        'validator': check_temporal_consistency
    },
    'cardinality_preservation': {
        'description': '1:1, 1:N relationships maintained',
        'weight': 0.1,
        'validator': check_cardinality
    },
    'semantic_equivalence': {
        'description': 'Clinical meaning preserved',
        'weight': 0.2,
        'validator': check_semantic_equivalence
    },
    'completeness': {
        'description': 'Required fields populated',
        'weight': 0.2,
        'validator': check_completeness
    }
}
```

---

## Phase 4: Highlander Protocol for Mapping Selection

### 4.1 Fitness Function Customization

Organisms compete based on mapping quality:

```python
def calculate_healthcare_fitness(organism, mapping_results):
    """
    Fitness = mapping_success_rate * (1 - avg_vp) * throughput_factor
    
    - mapping_success_rate: % of records successfully transformed
    - avg_vp: average violation pressure (lower = better)
    - throughput_factor: records processed per cycle
    """
    success_rate = mapping_results['successful'] / mapping_results['total']
    vp_score = 1.0 - mapping_results['avg_vp']
    throughput = min(1.0, mapping_results['throughput'] / TARGET_THROUGHPUT)
    
    return success_rate * vp_score * throughput
```

### 4.2 Battle Outcomes = Mapping Strategy Selection

When organisms battle:
- **Winner absorbs loser's vocabulary** = learns additional mapping patterns
- **Winner absorbs loser's VP history** = inherits validated transformations
- **Language head blend** = combines successful token sequences (mapping rules)

This naturally selects for organisms that:
1. Know more valid mappings (larger vocabulary)
2. Produce consistent transformations (low VP)
3. Handle edge cases (survived battles with specialists)

---

## Phase 5: Integration Architecture

### 5.1 System Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HEALTHCARE DATA LAKE                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ VistA    │  │ Epic     │  │ Cerner   │  │ Legacy   │           │
│  │ (MUMPS)  │  │ (HL7v2)  │  │ (HL7v2)  │  │ (COBOL)  │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │             │             │                   │
│       └─────────────┴─────────────┴─────────────┘                   │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              BUTTERFLY CONVERGENCE ENGINE                    │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  ORGANISM POPULATION (500 mapping specialists)       │    │   │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │    │   │
│  │  │  │ADT  │ │ORU  │ │Code │ │Date │ │Edge │          │    │   │
│  │  │  │Mapper│ │Mapper│ │Trans│ │Norm │ │Case │          │    │   │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘          │    │   │
│  │  │         ↕ HIGHLANDER BATTLES ↕                    │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                           │                                  │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  VP VALIDATION LAYER                                 │    │   │
│  │  │  - Referential integrity checks                      │    │   │
│  │  │  - Code system validation                            │    │   │
│  │  │  - Semantic equivalence scoring                      │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    FHIR R4 OUTPUT                            │   │
│  │  Unified, validated, VP-certified healthcare data            │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow

1. **Ingest**: Legacy records enter as "experiences" for organisms
2. **Process**: Organisms compete to transform records (Highlander selection)
3. **Validate**: VP system scores transformation consistency
4. **Output**: Winning transformations produce FHIR resources
5. **Learn**: Successful mappings reinforce organism vocabulary

---

## Phase 6: Implementation Roadmap

### Sprint 1: Foundation (Week 1-2)
- [ ] Complete Phase 0 stabilization
- [ ] Create healthcare vocabulary seed file (start with 10k terms)
- [ ] Add config.json vocabulary customization support
- [ ] Test vocabulary loading in existing system

### Sprint 2: Relations (Week 3-4)
- [ ] Implement healthcare semantic relations
- [ ] Add state/action word mappings
- [ ] Test organism language learning with domain terms
- [ ] Verify VP calculations on mock transformations

### Sprint 3: VP Customization (Week 5-6)
- [ ] Implement healthcare VP traits
- [ ] Create validation functions for each trait
- [ ] Test VP scoring on sample data transformations
- [ ] Tune VP weights based on domain requirements

### Sprint 4: Integration Layer (Week 7-8)
- [ ] Build input adapter for legacy formats (HL7v2, flat file)
- [ ] Build output adapter for FHIR R4
- [ ] Connect to sample data sources
- [ ] End-to-end transformation pipeline test

### Sprint 5: Production Hardening (Week 9-10)
- [ ] Performance optimization for production volumes
- [ ] Error handling and logging
- [ ] Monitoring dashboard customization
- [ ] Documentation and training materials

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Mapping accuracy | >95% | Records correctly transformed |
| VP consistency | <0.25 avg | Average VP across all mappings |
| Throughput | >1000 rec/sec | Records processed per second |
| Coverage | >90% | % of source fields mapped |
| Learning rate | Improving | VP decreasing over generations |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Vocabulary too small | Start with 10k, expand based on unmapped terms |
| VP too strict | Tune trait weights, allow VP1 for lossy transforms |
| Organisms overspecialize | Increase mutation rate, diversity tournaments |
| Performance bottleneck | Enable Ray distributed training |
| Edge cases missed | Log VP3 failures, add to training vocabulary |

---

## Appendix A: Sample Healthcare Vocabulary Categories

### A.1 HL7 v2.x Message Types
```
ACK, ADT, BAR, BPS, BRP, BRT, BTS, CCF, CCI, CCM, CCQ, CCU, CRM, CSU,
DFT, DOC, DSR, EAC, EAN, EAR, EHC, ESR, ESU, INR, INU, LSR, LSU, MDM,
MFD, MFK, MFN, MFQ, MFR, NMD, NMQ, NMR, OMB, OMD, OMG, OMI, OML, OMN,
OMP, OMS, OPL, OPR, OPU, ORA, ORB, ORD, ORF, ORG, ORI, ORL, ORM, ORN,
ORP, ORR, ORS, ORU, OSM, OSQ, OSR, OUL, PEX, PGL, PIN, PMU, PPG, PPP,
PPR, PPT, PPV, PRR, PTR, QBP, QCK, QCN, QRY, QSB, QSX, QVR, RAR, RAS,
RCI, RCL, RDE, RDR, RDS, RDY, REF, RER, RGR, RGV, ROR, RPA, RPI, RPL,
RPR, RQA, RQC, RQI, RQP, RRA, RRD, RRE, RRG, RRI, RSP, RTB, SCN, SDN,
SDR, SIU, SLN, SLR, SLS, SMD, SQM, SQR, SRM, SRR, SSR, SSU, STC, STI,
SUR, TBR, TCR, TCU, UDM, VXQ, VXR, VXU, VXX
```

### A.2 FHIR R4 Resource Types
```
Account, ActivityDefinition, AdverseEvent, AllergyIntolerance,
Appointment, AppointmentResponse, AuditEvent, Basic, Binary,
BiologicallyDerivedProduct, BodyStructure, Bundle, CapabilityStatement,
CarePlan, CareTeam, CatalogEntry, ChargeItem, ChargeItemDefinition,
Claim, ClaimResponse, ClinicalImpression, CodeSystem, Communication,
CommunicationRequest, CompartmentDefinition, Composition, ConceptMap,
Condition, Consent, Contract, Coverage, CoverageEligibilityRequest,
CoverageEligibilityResponse, DetectedIssue, Device, DeviceDefinition,
DeviceMetric, DeviceRequest, DeviceUseStatement, DiagnosticReport,
DocumentManifest, DocumentReference, EffectEvidenceSynthesis,
Encounter, Endpoint, EnrollmentRequest, EnrollmentResponse,
EpisodeOfCare, EventDefinition, Evidence, EvidenceVariable,
ExampleScenario, ExplanationOfBenefit, FamilyMemberHistory, Flag,
Goal, GraphDefinition, Group, GuidanceResponse, HealthcareService,
ImagingStudy, Immunization, ImmunizationEvaluation,
ImmunizationRecommendation, ImplementationGuide, InsurancePlan,
Invoice, Library, Linkage, List, Location, Measure, MeasureReport,
Media, Medication, MedicationAdministration, MedicationDispense,
MedicationKnowledge, MedicationRequest, MedicationStatement,
MedicinalProduct, MedicinalProductAuthorization,
MedicinalProductContraindication, MedicinalProductIndication,
MedicinalProductIngredient, MedicinalProductInteraction,
MedicinalProductManufactured, MedicinalProductPackaged,
MedicinalProductPharmaceutical, MedicinalProductUndesirableEffect,
MessageDefinition, MessageHeader, MolecularSequence, NamingSystem,
NutritionOrder, Observation, ObservationDefinition,
OperationDefinition, OperationOutcome, Organization,
OrganizationAffiliation, Patient, PaymentNotice, PaymentReconciliation,
Person, PlanDefinition, Practitioner, PractitionerRole, Procedure,
Provenance, Questionnaire, QuestionnaireResponse, RelatedPerson,
RequestGroup, ResearchDefinition, ResearchElementDefinition,
ResearchStudy, ResearchSubject, RiskAssessment, RiskEvidenceSynthesis,
Schedule, SearchParameter, ServiceRequest, Slot, Specimen,
SpecimenDefinition, StructureDefinition, StructureMap, Subscription,
Substance, SubstanceNucleicAcid, SubstancePolymer, SubstanceProtein,
SubstanceReferenceInformation, SubstanceSourceMaterial,
SubstanceSpecification, SupplyDelivery, SupplyRequest, Task,
TerminologyCapabilities, TestReport, TestScript, ValueSet,
VerificationResult, VisionPrescription
```

---

## Appendix B: Files to Create/Modify

### New Files
- `data/healthcare_vocabulary_50k.json` - Domain vocabulary
- `reality_simulator/healthcare_adapter.py` - Input/output adapters
- `reality_simulator/healthcare_vp_traits.py` - Custom VP validators
- `tests/test_healthcare_integration.py` - Domain-specific tests

### Modified Files
- `config.json` - Add vocabulary seed file path
- `reality_simulator/language/linguistic_knowledge_web.py` - Add healthcare relations
- `reality_simulator/refine_vocabulary.py` - Add healthcare DOMAIN_CORE
- `unified_entry.py` - Healthcare mode flag

---

*Document Version: 1.0*
*Created: December 3, 2025*
*Status: PENDING Phase 0 completion*
