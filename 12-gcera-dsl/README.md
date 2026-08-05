# GCERA-DSL v0.1.0

**Enterprise Description Language for RUOS**

وضعیت: `draft-implementable`

GCERA-DSL یک زبان توصیفی، انسان‌خوان و ماشین‌خوان برای تعریف موجودیت‌ها، صفحات، قابلیت‌ها، سفرها، جریان‌های کاری و سایر اشیای RUOS است. این زبان بر YAML/JSON سوار می‌شود، اما معنای آن مستقل از CMS، فریم‌ورک، پایگاه داده و مدل هوش مصنوعی است.

## 1. هدف

GCERA-DSL باید امکان دهد که:

- هر شیء سازمانی یک شناسه پایدار و معنای صریح داشته باشد.
- دانش داخل صفحه ذخیره نشود؛ صفحه فقط دانش را Assemble و Render کند.
- یک رکورد در مسیرهای متعدد، زبان‌های متعدد و کانال‌های متعدد استفاده شود.
- منشأ، نسخه، وضعیت، مالک، سطح اطمینان و تاریخچه هر داده قابل ردیابی باشد.
- Knowledge Graph، Capability Layer، Journey، SEO، AI و Design System از ابتدا جزئی از تعریف باشند.
- تولید HTML، WordPress، API، JSON-LD، جست‌وجو و پاسخ AI از یک منبع واحد انجام شود.

## 2. اصول قفل‌شده

1. `One Entity → One Canonical Record`
2. `Pages are views of knowledge, not containers of knowledge`
3. `Knowledge before content`
4. `Capability before service expression`
5. `Intent before assembly`
6. `Persian approval before localization`
7. `No canonical knowledge without provenance`
8. `No strategic publish without human approval`
9. `Approved versions are superseded, never silently overwritten`
10. `Rejected knowledge is archived with reason`

## 3. قالب سند

هر فایل GCERA-DSL یک سند مستقل است:

```yaml
ruos:
  spec: gcera-dsl
  version: 0.1.0
  document_id: doc:red-umbrella:structures-hub:v1
  namespace: red-umbrella
  language: fa
  status: draft
  provenance: {}

objects: []
```

## 4. گرامر معنایی

```ebnf
Document      ::= Header Object+
Header        ::= Spec Version DocumentID Namespace Language Status Provenance
Object        ::= Identity Semantics Relationships Governance Extensions
Identity      ::= UID Kind Name [Slug] [Aliases]
Semantics     ::= Summary [Description] [Intent] [Personas] [Attributes]
Relationships ::= Relationship*
Relationship  ::= Predicate Target [Qualifiers] [Evidence]
Governance    ::= Status Version Owner Sources Confidence Approval History
Page          ::= Object Route Assembly SEO AI Analytics Design
Assembly      ::= Block+
Block         ::= BlockID BlockType SourceSelector FieldProjection [Conditions] [CTA]
```

## 5. نوع‌های هسته

`kind` در نسخه 0.1 یکی از موارد زیر است:

- `organization`
- `brand`
- `project`
- `page`
- `entity`
- `structure`
- `structure_category`
- `capability`
- `service`
- `solution`
- `journey`
- `workflow`
- `task`
- `persona`
- `query`
- `search_intent`
- `location`
- `campaign`
- `investment`
- `article`
- `video`
- `guide`
- `faq`
- `project_case`
- `media`
- `component`
- `design_token`
- `rule`
- `decision`
- `evidence`
- `metric`
- `schema`

نوع‌های جدید فقط از طریق Extension و با Namespace مشخص اضافه می‌شوند.

## 6. شناسه‌ها

فرمت توصیه‌شده UID:

```text
<kind>:<namespace>:<canonical-slug>
```

نمونه:

```text
page:red-umbrella:structures
structure:red-umbrella:unipole
capability:red-umbrella:foundation-design
journey:red-umbrella:outdoor-structure-purchase
```

قواعد:

- UID بعد از انتشار Canonical تغییر نمی‌کند.
- تغییر نام نمایشی باعث تغییر UID نمی‌شود.
- هر Alias باید به UID Canonical Resolve شود.
- حذف فیزیکی شیء Canonical ممنوع است؛ فقط `deprecated` یا `archived` می‌شود.

## 7. مدل عمومی شیء

```yaml
- uid: structure:red-umbrella:unipole
  kind: structure
  name:
    fa: یونی‌پل
    en: Unipole
  slug: unipole
  aliases:
    fa: [تابلو یونی پل, پایه تبلیغاتی یک‌ستونه]
  status: approved
  version: 1.0.0
  summary:
    fa: سازه تبلیغات محیطی تک‌پایه با سطح نمایش مرتفع.
  intents: [learn, compare, purchase, invest, rent]
  personas:
    - persona:red-umbrella:municipality
  attributes: {}
  relationships: []
  knowledge: {}
  capabilities: []
  media: []
  seo: {}
  ai: {}
  governance: {}
```

## 8. مدل Relationship

```yaml
relationships:
  - predicate: belongs_to
    target: structure_category:red-umbrella:outdoor
    qualifiers:
      primary: true
    evidence:
      - evidence:red-umbrella:architecture-v2
```

Predicateهای هسته:

- `is_a`
- `belongs_to`
- `part_of`
- `contains`
- `uses`
- `requires`
- `supports`
- `solves`
- `serves`
- `suitable_for`
- `installed_at`
- `available_for`
- `related_to`
- `alternative_to`
- `complementary_to`
- `depends_on`
- `produces`
- `demonstrated_by`
- `references`
- `derived_from`
- `validated_by`
- `supersedes`
- `contradicts`
- `renders`

## 9. مدل Page

صفحه فقط View است و باید اشیای مرجع را Assemble کند.

```yaml
- uid: page:red-umbrella:structures
  kind: page
  page_type: hub
  route: /structures
  canonical_url: /structures
  primary_entity: entity:red-umbrella:structure-domain
  intents: [learn, explore, compare]
  personas: []
  mission:
    fa: دانشنامه و کاتالوگ مادر تمام سازه‌ها
  exclusions:
    - direct_sales_page
    - investment_page
    - rental_page
  assembly: []
```

### 9.1 Block

```yaml
assembly:
  - id: structures-grid
    type: entity_grid
    source:
      select:
        kind: structure
        namespace: red-umbrella
        status: [approved, canonical, published]
    fields:
      - name.fa
      - summary.fa
      - media.primary
      - attributes.orientation
      - attributes.face_count
      - attributes.lighting
    interactions:
      filters:
        - attributes.environment
        - attributes.orientation
        - attributes.face_count
        - attributes.lighting
    journey:
      next_best_actions:
        - journey:red-umbrella:indoor-structure-purchase
        - journey:red-umbrella:outdoor-structure-purchase
        - journey:red-umbrella:investment
        - journey:red-umbrella:campaign-rental
```

### 9.2 Blockهای استاندارد

- `hero`
- `executive_summary`
- `table_of_contents`
- `entity_grid`
- `entity_detail`
- `filter_bar`
- `comparison`
- `knowledge_graph`
- `capability_layer`
- `process`
- `evidence`
- `project_gallery`
- `media_gallery`
- `article_feed`
- `video_feed`
- `faq`
- `cta`
- `footer`

## 10. Knowledge Graph در صفحه

هر Page باید Graph Scope محلی داشته باشد:

```yaml
knowledge_graph:
  root: entity:red-umbrella:structure-domain
  include_predicates:
    - belongs_to
    - suitable_for
    - supports
    - available_for
    - related_to
    - requires
  depth: 2
  expose:
    visual: true
    internal_links: true
    json_ld: true
    ai_context: true
```

## 11. Capability Layer

```yaml
capability_layer:
  mode: contextual
  select:
    via_relationships:
      from: primary_entity
      predicates: [uses, requires, supported_by]
  render:
    fields:
      - name.fa
      - problem.fa
      - business_value.fa
      - process
      - evidence
      - related_services
  rule: capability_is_not_service
```

Capability باید توضیح دهد «چرا و چگونه قادر به حل مسئله‌ایم»؛ Service بیان خروجی تجاری قابل خرید است.

## 12. Journey

```yaml
journey:
  uid: journey:red-umbrella:outdoor-structure-purchase
  entry_intents: [purchase, compare]
  persona_refs:
    - persona:red-umbrella:municipality
    - persona:red-umbrella:organization
  stages:
    - discover
    - understand
    - compare
    - capability_validation
    - consultation
    - quotation
    - purchase
  primary_conversion: quotation
```

## 13. SEO و AI

```yaml
seo:
  query_refs: []
  intent_refs: []
  title:
    fa: سازه‌های تبلیغاتی؛ مرجع انواع، کاربردها و مشخصات
  meta_description:
    fa: مرجع شناخت و مقایسه انواع سازه‌های تبلیغاتی، کاربرد، ابعاد، نورپردازی، فونداسیون و مسیرهای خرید، سرمایه‌گذاری و اجاره.
  canonical: /structures
  schemas:
    - CollectionPage
    - ItemList
    - BreadcrumbList
    - FAQPage

ai:
  entity_summary: true
  citation_ready: true
  chunk_strategy: semantic_sections
  expose_relationships: true
  answer_questions: []
```

## 14. Provenance و Governance

```yaml
provenance:
  sources:
    - source_id: conversation:red-umbrella:structure-final
      type: conversation
      status: user_confirmed
    - source_id: document:red-umbrella:architecture-v1
      type: spreadsheet
  extracted_at: 2026-08-05

governance:
  owner: role:red-umbrella:website-director
  reviewer: role:red-umbrella:architecture-reviewer
  approver: person:red-umbrella:owner
  confidence: 0.98
  approval:
    state: approved
    date: 2026-08-05
  history: []
```

## 15. وضعیت‌ها

- `draft`
- `review`
- `approved`
- `canonical`
- `published`
- `superseded`
- `deprecated`
- `archived`
- `rejected`

## 16. نسخه‌بندی

- نسخه سند: Semantic Versioning
- نسخه هر Object: مستقل از نسخه سند
- تغییر ناسازگار معنایی: Major
- افزودن فیلد اختیاری یا Predicate: Minor
- اصلاح متن، نمونه یا خطای بدون تغییر معنا: Patch

## 17. قواعد اعتبارسنجی اجباری

یک سند معتبر باید:

- `ruos.spec = gcera-dsl` داشته باشد.
- `ruos.version` معتبر داشته باشد.
- `document_id` یکتا داشته باشد.
- حداقل یک Object داشته باشد.
- UID تمام Objects یکتا باشد.
- Target تمام Relationshipها قابل Resolve باشد یا `external: true` داشته باشد.
- هر Page دارای `route`, `primary_entity`, `intents` و `assembly` باشد.
- هر Object Canonical دارای Source و Owner باشد.
- هر تغییر Canonical تاریخچه داشته باشد.
- هر CTA با Journey و Intent سازگار باشد.
- داده فنی فاقد منبع به‌عنوان Fact Canonical منتشر نشود.

## 18. خروجی‌های هدف

GCERA-DSL باید بتواند مستقیماً به این خروجی‌ها Compile شود:

- HTML/CSS/JS
- WordPress content model
- REST/GraphQL resources
- JSON-LD
- Schema.org
- Search index
- Vector index
- Knowledge Graph
- AI context chunks
- Sitemap
- Internal-link graph
- Design component props
- QC report

## 19. فایل‌های این بسته

- `schemas/gcera-dsl-v0.1.schema.json`
- `examples/red-umbrella-structures-hub.yaml`
- `examples/red-umbrella-unipole.yaml`

## 20. مرحله بعد

پس از تثبیت GCERA-DSL:

1. Canonical Repository Specification
2. Enterprise Assembly Engine
3. Enterprise Runtime
4. Production Page Generation
