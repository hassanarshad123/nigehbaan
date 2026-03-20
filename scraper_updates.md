# Nigehbaan expansion: 145+ Pakistan child protection data sources mapped

**Pakistan's child protection data ecosystem is fragmented across 145+ sources spanning government agencies, international organizations, NGOs, academic databases, social media platforms, and law enforcement tools — but most are scrapable.** This inventory identifies every verified data source across all 11 exploitation categories, with exact URLs, formats, scraping feasibility, geographic granularity, and integration architecture. The highest-value sources are the US DOL annual Pakistan report, Sahil's Cruel Numbers PDFs, NCMEC CyberTipline country data, ILOSTAT's REST API, and the Justice Project Pakistan open data portal. Critical gaps include the absence of a Pakistani INHOPE hotline, no unified national missing children database, and zero confirmed deployments of PhotoDNA, Thorn, or Project VIC within Pakistani law enforcement.

---

## Category 1: Child sexual abuse and exploitation

### Sahil NGO — the single most important domestic CSA data source
- **URL**: https://sahil.org/cruel-numbers/
- **PDFs**: `https://sahil.org/wp-content/uploads/2020/03/Cruel-Numbers-2019-final.pdf` (pattern applies to all years)
- **Data**: Annual "Cruel Numbers" reports published since 2003, compiled from **81 newspapers**. Tracks rape, sodomy, gang rape, gang sodomy, attempted rape, child marriages, murder after abuse. Provides gender breakdowns, age-group analysis, province-wise distribution (Punjab, Sindh, KP, Balochistan, ICT, AJK, GB), urban/rural divide, abuser categories, relationship to victim, location of abuse, and FIR registration status. 2025 data: **3,630 cases** (8% increase). Also publishes semi-annual mid-year reports and a Violence Against Women dataset (7,071 GBV cases in 2025).
- **Format**: PDF on WordPress (wp-content/uploads). Predictable URL patterns.
- **Scraping feasibility**: HIGH. PDFs publicly accessible without authentication. Tables extractable via tabula/pdfplumber. WordPress catalog page scrapable for discovery.
- **Geographic granularity**: Provincial consistently; some district-level; urban/rural.
- **Update frequency**: Annual + semi-annual.
- **Integration**: PDF scraper pipeline → table extraction → time-series database. Monitor catalog page for new uploads.

### Pakistani court databases
- **Supreme Court**: https://supremecourt.nadra.gov.pk/judgement-search/ — searchable by case type
- **Punjab District Courts**: https://dsj.punjab.gov.pk/ — Case Management System
- **Sindh District Courts**: https://cases.districtcourtssindh.gos.pk/ — CFMS search
- **Sindh High Court**: https://sindhhighcourt.gov.pk/ — monthly progress reports
- **Pakistan Legal Database**: https://www.paklegaldatabase.com/case-status/ — aggregated links
- **Data**: Case status, hearing dates, cause lists, some uploaded judgments. No dedicated PPC 292-294/375-377 filter. Must search by case type or keyword.
- **Format**: Dynamic HTML (ASP.NET, PHP). Judgments in PDF. No API.
- **Scraping feasibility**: LOW-MEDIUM. Dynamic forms require Selenium/Playwright. Some have CAPTCHA. No bulk download.
- **Geographic granularity**: Court/district level.
- **Integration**: Targeted form-submission scraping with headless browser. Very labor-intensive.

### ECPAT International — Pakistan
- **Country page**: https://ecpat.org/country/pakistan/
- **Global Boys Initiative Pakistan Report (2022)**: https://ecpat.org/wp-content/uploads/2022/03/Gobal-Boys-Initiative_Pakistan-Report_FINAL.pdf
- **South Asia Regional Overview**: https://ecpat.org/wp-content/uploads/2021/05/Regional-Overview_South-Asia.pdf
- **Supplementary report**: https://pahchaan.info/wp-content/uploads/2025/05/Supplementary-report-on-Sexual-Exploitation-of-Children-in-Pakistan.pdf
- **Data**: Comprehensive country assessments covering legal frameworks, prevalence data, government responses, CSAM statistics. Pakistan Boys Report contains survey data from 63 frontline workers.
- **Format**: PDF on WordPress CMS. HTML country page with GPI indicators.
- **Scraping feasibility**: HIGH. PDFs freely downloadable. HTML scrapable for GPI data.
- **Update frequency**: Every 3-5 years per country.

### Pahchaan.info (ECPAT Pakistan partner)
- **URL**: http://www.pahchaan.info/about.php
- **Annual report**: https://pahchaan.info/wp-content/uploads/2025/05/PAHCHAAN-ANNUAL-REPORT-2021-Final.pdf
- **Data**: Hospital-based child protection unit data (10+ years from Children Hospital Lahore — first such unit in South Asia). Annual case statistics. Research publications.
- **Format**: WordPress/PHP site with PDF reports.
- **Scraping feasibility**: MEDIUM. PDFs downloadable; limited structured online data.
- **Geographic granularity**: Primarily Punjab/Lahore.

### UNICEF Pakistan child protection
- **Main**: https://www.unicef.org/pakistan/child-protection-0
- **COP situation analysis**: https://www.unicef.org/pakistan/documents/situation-analysis-child-online-protection-pakistan
- **UNICEF DATA**: https://data.unicef.org/topic/child-protection/overview/
- **2024 VAC mapping study (NCSW)**: https://ngdp-ncsw.org.pk/storage/6865729cf1528.pdf
- **Data**: Birth registration (34%), child labor (3.3M children), child marriage (18% girls), MICS survey data. The **2024 VAC mapping study contains province-level case data** — Punjab: 2,506 CSA cases; KP: 366.
- **Format**: HTML + PDF reports. UNICEF DATA provides structured CSV/Excel downloads and SDMX REST API.
- **Scraping feasibility**: HIGH for data.unicef.org. MEDIUM for country reports.
- **Integration**: UNICEF SDMX API at https://sdmx.data.unicef.org/ for programmatic access.

### Punjab Forensic Science Agency
- **URL**: https://pfsa.punjab.gov.pk/
- **Data**: DNA database with ~30,000 profiles. Handled major CSA cases (Zainab, Chunian, Motorway rape). Academic papers on DNA database published in forensic journals.
- **Scraping feasibility**: LOW. No public reports or statistics. Academic publications behind paywalls. RTI requests needed.

### Kasur child abuse documentation
- **Dawn archives**: https://www.dawn.com/news/1473645 and extensive coverage
- **UNICEF statement**: https://www.unicefusa.org/press/reports-sexual-abuse-children-kasur-pakistan
- **Data**: 2015 Hussain Khanwala scandal: **280+ child victims, 400+ pornographic videos**. 2018 Zainab Ansari case led to Zainab Alert Act. No centralized database.
- **Scraping feasibility**: MEDIUM. News archives scrapable; government documents as PDFs.

### Government child protection infrastructure
- **NCRC**: https://ncrc.gov.pk/ — First State of Children Report 2024: https://ncrc.gov.pk/wp-content/uploads/2025/04/State-of-Children-V2.pdf
- **NCRC Annual Report 2024-25**: https://ncrc.gov.pk/wp-content/uploads/2025/07/Annual-Report-24-25.pdf
- **NCRC street children policy brief**: https://ncrc.gov.pk/wp-content/uploads/2025/03/POLICY-BRIEF_Street-connected-Children-in-Pakistan.pdf
- **Punjab CPWB**: https://cpwb.punjab.gov.pk/ — Helpline 1121, 9 Child Protection Institutions
- **KP CPWC**: https://kpcpwc.gov.pk/ — **CPIMS database with 27,000+ cases** (internal, not public)
- **Scraping feasibility**: HIGH for NCRC PDFs. LOW for internal systems (CPIMS, CPWB helpline data).

---

## Category 2: Online child exploitation

### FIA Cybercrime Wing / NCCIA
- **URL**: https://www.fia.gov.pk/ccw
- **Complaint portal**: https://complaint.fia.gov.pk/
- **NCCIA (successor)**: https://www.nccia.gov.pk/
- **Data**: As of May 2024, FIA Cybercrime Wing replaced by National Cyber Crime Investigation Agency under PECA Section 51. Reported **266 daily cybercrimes against children**. Pakistan joined Interpol's ICSE database as 71st country. 15 Cybercrime Reporting Centers across 6 zones.
- **Format**: HTML informational pages. Complaint portal is submission-only.
- **Scraping feasibility**: LOW. No public case databases or statistics. Press releases only.
- **Integration**: Scrape press releases; monitor news outlets for cited statistics; RTI requests.

### PTA content blocking data
- **URL**: https://www.pta.gov.pk/
- **Data**: Under PECA Section 37, PTA blocked **5,175 CSAM websites** via NCCIA Interpol desk. **1 million+ URLs blocked** for immoral content. 2025 report: 102,010 URLs processed, 25,677 blocked. Platform compliance: YouTube 83.81%, Instagram 80.38%, Facebook 79.77%, TikTok 71.55%, **X/Twitter only 35.18%**.
- **Scraping feasibility**: MEDIUM. No dedicated public data portal. Statistics published in parliamentary responses via news outlets (ProPakistani, TechJuice).
- **Integration**: News scraping from tech outlets for PTA statistics; monitor pta.gov.pk for annual reports.

### NCMEC CyberTipline — Pakistan data
- **Data page**: https://www.missingkids.org/gethelpnow/cybertipline/cybertiplinedata
- **Country PDFs**: https://www.missingkids.org/content/dam/missingkids/pdfs/2022-reports-by-country.pdf
- **Global Platform**: https://globalchildexploitationpolicy.org/legal-summaries/pakistan
- **Data**: Pakistan received **5.4 million CSAM reports (2020-2022)**, ranking **3rd globally** after India and Philippines. 2024 total: **20.5 million reports** globally (84% resolve outside US).
- **Format**: Annual PDFs with country breakdowns. Global Platform provides interactive jurisdiction-level data.
- **Scraping feasibility**: HIGH. PDFs freely downloadable.
- **Integration**: PDF parsing for annual reports; register for Global Platform for granular analytics.

### IWF Pakistan reporting portal
- **Research**: https://www.iwf.org.uk/about-us/why-we-exist/our-research/
- **Pakistan portal (English)**: https://report.iwf.org.uk/pk/
- **Pakistan portal (Pashto)**: https://report.iwf.org.uk/pk_ps/
- **Data**: IWF operates Pakistan-specific CSAM reporting portal in 3 languages (partnership with Digital Rights Foundation). 2023: **275,652 confirmed CSAM URLs** globally.
- **Scraping feasibility**: HIGH for annual reports. Portal is submission-only.

### Meta and Google transparency reports
- **Meta government requests**: https://transparency.meta.com/reports/government-data-requests/ (filterable by Pakistan)
- **Meta integrity reports**: https://transparency.meta.com/reports/integrity-reports-q1-2025/
- **Google Pakistan government removals**: https://transparencyreport.google.com/government-removals/by-country/PK
- **Data**: Meta is largest CSAM reporter (90%+ of NCMEC reports). Q1 2025: 1.7M reports. Google provides Pakistan-specific government content removal requests with compliance rates.
- **Scraping feasibility**: HIGH. Structured, filterable portals. CSV downloads available for government requests.

### Digital Rights Foundation
- **URL**: https://digitalrightsfoundation.pk/
- **Data**: Monthly newsletter with helpline statistics (e.g., "263 complaints in November, 134 from women"). Runs Pakistan's IWF CSAM reporting portal. Helpline: 0800-39393.
- **Scraping feasibility**: HIGH. WordPress site; monthly newsletters with structured helpline data.

### WeProtect Global Alliance
- **GTA 2025**: https://www.weprotect.org/global-threat-assessment-25/
- **GTA 2025 PDF**: https://www.weprotect.org/wp-content/uploads/GTA-2025_EN.pdf
- **Data page**: https://www.weprotect.org/global-threat-assessment-23/data/
- **Data**: Biennial Global Threat Assessments (2019-2025). Pakistan-specific data embedded within reports.
- **Scraping feasibility**: HIGH for PDFs; MEDIUM for interactive data pages (JS-rendered).

### Bytes for All Pakistan
- **URL**: https://bytesforall.pk/publications
- **Data**: Annual Internet Landscape Report. Internet shutdown tracker at www.killswitch.pk.
- **Scraping feasibility**: HIGH. Standard website with downloadable reports.

### ITU Child Online Protection
- **URL**: https://www.itu.int/en/ITU-D/Cybersecurity/Pages/COP/COP.aspx
- **Workshop report**: https://www.itu.int/en/ITU-D/Regional-Presence/AsiaPacific/Documents/Child%20Online%20Protection%20Asia%20and%20the%20Pacific%20Concluding%20Workshop%20Conference%20Report.pdf
- **Data**: Pakistan is a beneficiary of ITU COP Asia-Pacific programme. National COP assessment completed 2025.
- **Scraping feasibility**: MEDIUM. PDF reports accessible.

---

## Category 3: Child labor and bonded labor

### US DOL Findings on Worst Forms of Child Labor — the gold standard
- **Pakistan page**: https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan
- **2024 PDF**: https://www.dol.gov/sites/dolgov/files/ILAB/child_labor_reports/tda2024/Pakistan.pdf
- **2023 PDF**: https://www.dol.gov/sites/dolgov/files/ILAB/child_labor_reports/tda2023/Pakistan.pdf
- **Data**: **The single most comprehensive annual source**. Statistics on children's work/education (Table 1), work by sector/activity (Table 2), laws (Tables 3-4), enforcement data (Table 6 — inspectors, inspections, violations, arrests by province). Covers all sectors: brick kilns, agriculture, fishing, mining, carpets, surgical instruments, glass bangles, domestic work, auto workshops, begging. Punjab: **85,000+ inspections** (2023).
- **Format**: PDF with consistently formatted tables. URL pattern: `/tda{YEAR}/Pakistan.pdf`.
- **Scraping feasibility**: EXCELLENT. Historical data from 2003-2024.
- **Integration**: PDF table extraction → time-series database. Automated annual download.

### US DOL TVPRA List of Goods
- **Excel download**: https://www.dol.gov/sites/dolgov/files/ilab/child_labor_reports/tda2023/2024ListofGoodsExcel.xlsx
- **PDF**: https://www.dol.gov/sites/dolgov/files/ILAB/child_labor_reports/tda2023/2024-tvpra-list-of-goods.pdf
- **Pakistan entries (2024)**: Bricks (CL+FL), Carpets (CL+FL), Coal (CL), Cotton (CL), Glass Bangles (CL), Leather (CL), Surgical Instruments (CL), Baked goods (CL), Bovines (CL), Dairy products (CL), Electronics (CL), Furniture (CL), Garments (CL), Rice (CL), Textiles (CL).
- **Scraping feasibility**: EXCELLENT. Excel directly downloadable and machine-readable.

### ILOSTAT child labour statistics
- **URL**: https://ilostat.ilo.org/topics/child-labour/
- **API endpoint**: `https://rplumber.ilo.org/data/indicator/?id=SDG_B871_SEX_AGE_RT_A&lang=en&type=label&format=.csv`
- **Data**: SDG 8.7.1 indicator, children in economic activity by sex/age/sector, hazardous work statistics.
- **Format**: CSV, XLSX, DTA (Stata). REST API with programmatic access.
- **Scraping feasibility**: EXCELLENT. Direct download links with structured API.
- **Integration**: ILOSTAT API → database ingestion. Real-time updates.

### Provincial child labour surveys — district-level treasure troves
- **Punjab (2019-2020)**: https://labour.punjab.gov.pk/system/files/Punjab%20Child%20Survey%20KFR%20Report_0.pdf — **13.4% child labour prevalence** (5-14), all 36 districts. Agriculture 61.5%.
- **Sindh (2022-2024)**: https://dglabour.gos.pk/wp-content/uploads/2025/07/SCLS_KFR_02.07.2025.pdf — **~1.3 million children** in child labour, 29 districts, 61,859 household sample.
- **KP (2022)**: Released January 2024 — **9% of children 5-17** (745,440 children). Some areas up to 30%.
- **1996 National baseline**: http://www.ilo.org/wcmsp5/groups/public/---asia/---ro-bangkok/---sro-new_delhi/documents/publication/wcms_436435.pdf — 3.3M children (8.3%).
- **Scraping feasibility**: MODERATE. PDFs downloadable; tables require extraction via tabula/camelot.

### Brick kiln geospatial and census data
- **Zenodo GPS dataset**: https://zenodo.org/records/14038648 — First geospatial mapping of ALL brick kiln sites in Pakistan's Indo-Gangetic Plain. Precise GPS coordinates, emissions data. **Open access, CC license.**
- **Punjab Brick Kiln Census Dashboard**: http://dashboards.urbanunit.gov.pk/brick_kiln_dashboard/ — ~10,000 kilns, **126,766 children**, school enrollment status.
- **Open Data Pakistan**: https://opendata.com.pk/dataset/brick-kilns-census-punjab
- **ILO Working Paper**: https://www.ilo.org/media/316696/download
- **Format**: Zenodo is CSV/GeoJSON (EXCELLENT). Dashboard is dynamic JS (requires API reverse-engineering).
- **Integration**: Zenodo direct download → GIS integration. Dashboard requires Selenium scraping or API discovery.

### Sector-specific ILO studies
- **Carpet weaving**: https://www.ilo.org/sites/default/files/wcmsp5/groups/public/@ed_mas/@eval/documents/publication/wcms_149870.pdf — Districts: Faisalabad, Sheikhupura, Lahore, Multan.
- **Surgical instruments (Sialkot)**: https://www.dol.gov/sites/dolgov/files/ILAB/research_file_attachment/Pakistan%20redacted%20for%20web.pdf — ~5,000 children.
- **Sports goods (Sialkot Atlanta Agreement)**: https://www.ilo.org/media/330831/download — IMAC registered 224 firms, 1,997 stitching centers. ~7,000-15,000 children pre-intervention.
- **Domestic work**: https://www.ilo.org/sites/default/files/wcmsp5/groups/public/@asia/@ro-bangkok/@ilo-islamabad/documents/publication/wcms_851153.pdf — 10% of child labourers in domestic work. Rapid survey of 6 cities.
- **Auto workshops**: https://www.ilo.org/resource/news/rapid-assessment-child-labour-auto-mechanic-workshops
- **Agriculture/cotton**: https://www.ilo.org/media/361701/download
- **Mining (Balochistan coal/salt)**: https://www.ilo.org/wcmsp5/groups/public/---ed_norm/---declaration/documents/publication/wcms_082032.pdf — Coal mines (Shahrag, Chamalang, Quetta), salt mines (Khewra). **100-200 miner deaths/year**.

### BLLF and Punjab Labour Department
- **BLLF**: https://www.bllfpk.com/ — **85,000+ bonded labourers freed** since 1990 (45% children). 16 Punjab districts.
- **FES/BLLF report**: https://library.fes.de/pdf-files/bueros/pakistan/10382.pdf
- **Punjab Labour**: https://labour.punjab.gov.pk/ — LIMS dashboard, brick kiln survey data, **85,000+ inspections in 2023**, 8,580 brick kiln inspections with 771 violations.

---

## Category 4: Child marriage and forced marriage

### UNICEF and DHS structured data — API-accessible
- **UNICEF data portal**: https://data.unicef.org/topic/child-protection/child-marriage/ — **18% married before 18**, provincial breakdowns. SDMX API: https://sdmx.data.unicef.org/
- **DHS 2017-18**: https://dhsprogram.com/data/dataset/Pakistan_Standard-DHS_2017.cfm — **29% married by 18; 13% of 15-19 married**. DHS API: https://api.dhsprogram.com/ (JSON). STATcompiler: https://www.statcompiler.com/
- **MICS Punjab 2024**: https://mics.unicef.org/sites/mics/files/2025-01/Pakistan%202024%20MICS%20(Punjab)%20KFR.pdf — Key Findings just released January 2025.
- **MICS Sindh 2018-19**: http://sindhbos.gov.pk/mics/ — District-level microdata.
- **Scraping feasibility**: EXCELLENT. APIs provide JSON. Microdata downloadable after free registration.

### Girls Not Brides and child marriage atlas
- **URL**: https://www.girlsnotbrides.org/learning-resources/child-marriage-atlas/regions-and-countries/pakistan/
- **Data**: Prevalence, drivers (swara/badal/watta satta/pait likkhi customs), legal framework, economic impact.
- **Scraping feasibility**: HIGH. Well-structured HTML.

### Centre for Social Justice — forced conversion tracking
- **URL**: https://csjpak.org/publication.php
- **Human Rights Observer 2025**: https://csjpak.org/human-rights-observer-newsletter/Human-Rights-Observer-2025.pdf
- **Forced conversions paper**: https://csjpak.org/publications/Working-Paper-on-Forced-Conversions-silence-of-LambII.pdf
- **Data**: **515+ cases of abduction/forced conversion of minority girls** (2021-2025). Hindu girls = 69% of victims. **50%+ aged 14-18; 20% under 14**. Also tracks 2,793 blasphemy accused (1987-2024).
- **Scraping feasibility**: HIGH. Publication page with direct PDF downloads.

### UNFPA Pakistan
- **URL**: https://pakistan.unfpa.org/en/topics/child-marriage-4
- **Sindh PEA**: https://pakistan.unfpa.org/sites/default/files/pub-pdf/unfpa_child_marriage_pea_report_sindh.pdf — District-level analysis; **14/29 Sindh districts saw *increases* in child marriage**.

### Aurat Foundation and Shirkat Gah
- **Aurat Foundation**: https://www.af.org.pk/ — Annual reports, VAW data across 128 districts.
- **Shirkat Gah**: https://shirkatgah.org.pk/ — OHCHR submission: https://www.ohchr.org/sites/default/files/Documents/Issues/Women/WRGS/ForcedMarriage/NGO/WomensResourceCentrePakistan.docx
- **Scraping feasibility**: LOW-MEDIUM. PDFs require individual download.

---

## Category 5: Street children and begging mafias

### NCRC — first comprehensive national data
- **State of Children Report 2024**: https://ncrc.gov.pk/wp-content/uploads/2025/04/State-of-Children-V2.pdf — 862 CSA cases in H1 2024, 668 abductions, 82 missing children, 18 child marriages.
- **Street children policy brief**: https://ncrc.gov.pk/wp-content/uploads/2025/03/POLICY-BRIEF_Street-connected-Children-in-Pakistan.pdf — **1.5 million street children**. City estimates: Karachi 8,000-12,000; Lahore ~7,000; Rawalpindi ~3,000; Peshawar ~5,000; Quetta ~2,500.
- **Scraping feasibility**: HIGH. Direct PDF downloads.

### State of Children portal
- **URL**: https://stateofchildren.com/ — Comprehensive portal with dedicated sections on street children, trafficking, child labour. Provincial filtering.
- **Datasets**: https://stateofchildren.com/children-dataset/ — Structured data tables.
- **Scraping feasibility**: HIGH. Clean HTML structure.

### Major welfare organizations
- **Edhi Foundation**: https://www.edhi.org/children-services — 15+ shelters, baby cradles (Jhoolas). No quantitative public data.
- **SOS Pakistan**: https://www.sos.org.pk/ — 15 villages, 4 children's homes, 13 youth homes across 16 cities.
- **Chhipa Foundation**: https://www.chhipa.org/ — Karachi-based orphanages and baby cradles.
- **Azad Foundation**: https://azadfoundation.org/ — 170,900+ direct beneficiaries since 2001. Biometric registration system.
- **SPARC**: https://sparcpk.org/ — Annual State of Pakistan's Children reports since 1990s.
- **Scraping feasibility**: MEDIUM across all. Descriptive HTML, annual reports as PDFs.

### ILO begging mafia research
- **2004 rapid assessment**: By Collective for Social Science Research, Karachi. Found **34% of beggars under organized operations; 92% of 130 child beggars forced**.
- **Beggarization thesis (CORE)**: https://core.ac.uk/download/pdf/213396191.pdf
- **LUMS policy analysis**: https://cbs.lums.edu.pk/student-research-series/control-begging-pakistan-policy-analysis
- **Peshawar study (2024)**: https://migrationletters.com/index.php/ml/article/download/9237/6012/23408

### Provincial child protection bureaus
- **Punjab CPWB**: https://cpwb.punjab.gov.pk/ — 9 Child Protection Institutions, Open Reception Centers, **9,673 children rescued in 2022**.
- **KP CPWC**: https://kpcpwc.gov.pk/ — **CPIMS with 27,000+ registered cases** (2011-2016). Zamung Kor houses ~150 street children.
- **Scraping feasibility**: LOW for internal systems; MEDIUM for website content.

---

## Category 6: Organ trafficking involving children

### NCHR study — most comprehensive domestic source
- **URL**: https://nchr.gov.pk/wp-content/uploads/2023/09/Study-on-the-Exploitative-Trade-and-Transplantation-of-Organs-in-Pakistan.pdf
- **Data**: Legal framework, FIR cases, HOTA implementation review.
- **Scraping feasibility**: HIGH. Direct PDF download.

### HOTA and provincial transplant authorities
- **Federal HOTA**: https://hota.gov.pk/ — Minimal content, site frequently times out.
- **Punjab PHOTA**: https://phota.punjab.gov.pk/ — Hospital registration, recipient registry, 42 authorized hospitals.
- **KP MTRA**: https://kpmtra.gov.pk/ — Provincial transplant registry.
- **Data**: 1,721 kidney transplants (2007-2009) from 28 authorized hospitals.

### Global Observatory on Donation and Transplantation
- **2023 report**: https://www.transplant-observatory.org/wp-content/uploads/2024/12/2023-data-global-report-17122024.pdf
- **2024 report**: https://www.transplant-observatory.org/wp-content/uploads/2025/12/2024-data-global-report.pdf
- **IRODaT**: https://www.irodat.org/ — Pakistan 2024 data listed.
- **Data**: Standardized annual questionnaire data on donors, transplants, waitlisting, legislation.

### WHO and Declaration of Istanbul
- **WHO EMRO**: https://www.emro.who.int/emhj-volume-16-2010/volume-16-supplement/article-20.html — Hospital-level transplant data.
- **DICG**: https://www.declarationofistanbul.org/ — Pre-2008: **foreigners received 2/3 of 2,000 annual kidney transplants** in Pakistan.

### 2024 Rawalpindi case — children targeted
- **CBS News**: https://www.cbsnews.com/news/organ-trafficking-ring-bust-missing-boy-kidney-removed-pakistan/ — 14-year-old boy, kidney removed in underground lab, 6 arrested, kidneys sold for 900,000 PKR (~$4,000).
- **Academic**: https://www.assajournal.com/index.php/36/article/view/458 — Documents "Faisalabad Kidney Villages."

---

## Category 7: Child domestic violence and corporal punishment

### Sahil Cruel Numbers (cross-references Category 1)
Already documented above. Contains the most structured annual child violence data for Pakistan.

### Madadgaar Helpline — massive untapped dataset
- **URL**: http://madadgaar.org/
- **Data**: **223,000+ calls and 47,000+ cases over 19 years**. Data collected under 71 categories (16 computerized). Covers domestic violence, missing children, physical abuse, rape, sodomy, trafficking, kidnapping, forced marriage, karo-kari, torture. Provincial breakdowns.
- **Scraping feasibility**: MEDIUM. Statistics shared via press conferences; news scraping feasible. Formal data partnership recommended for full access.

### Corporal punishment tracking
- **URL**: https://endcorporalpunishment.org/reports-on-every-state-and-territory/pakistan/
- **PDF**: http://www.endcorporalpunishment.org/wp-content/uploads/country-reports/Pakistan.pdf
- **Data**: Legal status by setting (home, school, alternative care, penal), provincial breakdown, UPR/CRC recommendations. **75% of schools practice corporal punishment; 94% of children report daily punishment**.
- **Scraping feasibility**: HIGH. Well-structured HTML and text-based PDF.

### War Against Rape (WAR)
- **Facebook**: https://www.facebook.com/WarAgainstRape1989/ (website defunct — domain repurposed)
- **Data**: **1,256 medico-legal examinations** from 3 Karachi hospitals (2021-2022). 66 child cases mapped to Karachi neighborhoods.
- **Scraping feasibility**: LOW. Data via news reports only.

### Rozan and Dastak
- **Rozan**: https://rozan.org/ — Counseling helpline, child protection programs.
- **Dastak**: https://dastak.org.pk/ — 8,000+ women served since 1996; capacity 25 women + 45 children.
- **Scraping feasibility**: LOW for both. Narrative content, no public datasets.

---

## Category 8: Juvenile justice

### Justice Project Pakistan — open data platform
- **Data portal**: https://data.jpp.org.pk/
- **Reports**: https://www.jpp.org.pk/reports-and-publications
- **Prison data report 2024**: https://nchr.gov.pk/wp-content/uploads/2025/01/prison-data-report-2025.pdf
- **Data**: **The most comprehensive prison/juvenile justice dataset in Pakistan**. Open-source dashboards on prison statistics including juvenile data. Primary data from ALL provincial prison departments. Death row data. Age determination under JJSA. 1.7% of 102,026 prisoners are juveniles.
- **Format**: HTML dashboards, HURIDOCS platform (data.jpp.org.pk), PDF reports.
- **Scraping feasibility**: HIGH. Purpose-built open data platform.

### SPARC/State of Children juvenile data
- **Dataset**: https://stateofchildren.com/children-dataset/
- **Data**: 645 juveniles in Punjab (March 2022). **81% undertrial, 19% convicted**. Facility breakdown: Bahawalpur 61%, Faisalabad 25%. Offense types: murder 26%, unnatural offence 26%, rape 25%.
- **Scraping feasibility**: HIGH. Well-structured HTML data tables.

### World Prison Brief
- **URL**: https://www.prisonstudies.org/country/pakistan
- **Data**: Total prison population, rate per 100,000, **64.5% pre-trial**, 1.7% juveniles, occupancy rates, trend data from 2000.
- **Scraping feasibility**: HIGH. Structured HTML, monthly updates.

### Punjab Borstal Institutions
- **Faisalabad**: https://prisons.punjab.gov.pk/Borstal_Institution_and_Juvenile_Jail_Faisalabad
- **Bahawalpur**: https://prisons.punjab.gov.pk/Borstal_Institution_and_Juvenile_Jail_Bahawalpur
- **PMIS system**: https://pitb.gov.pk/pmis — Internal database, not public.
- **Scraping feasibility**: LOW. Administrative info only.

### JJSA 2018 implementation tracking
- **Full text**: https://sja.gos.pk/assets/library/acts/jjsa2018.pdf
- **RSIL analysis**: https://rsilpak.org/wp-content/uploads/2023/11/Juvenile-Justice-System-Act-2018_-A-Practical-Overview-of-Legal-Assistance-Determination-of-Age-and-Disposal-Through-Diversion.pdf
- **Stateofchildren.com**: https://stateofchildren.com/jjsa2018/
- **Pilot data**: 33/79 cases decided in 9 months (Lahore); 40/100 cases in 45 days (Peshawar).

---

## Category 9: Cross-border exploitation

### US TIP Report — structured annual intelligence
- **2025**: https://www.state.gov/reports/2025-trafficking-in-persons-report/pakistan/
- **2024**: https://www.state.gov/reports/2024-trafficking-in-persons-report/pakistan/
- **Data**: 2024: **1,607 trafficking cases investigated** (523 sex trafficking, 915 forced labor, 169 unspecified); 1,310 prosecuted; 495 convicted.
- **Scraping feasibility**: VERY HIGH. Well-structured HTML with consistent year-over-year formatting.

### China-Pakistan forced marriage trafficking
- **Brookings**: https://www.brookings.edu/articles/bride-trafficking-along-the-china-pakistan-economic-corridor/ — Full PDF: https://www.brookings.edu/wp-content/uploads/2022/03/FP_20220317_bride_trafficking_afzal.pdf
- **AP investigation (2019)**: **629 Pakistani girls/women sold as brides** to Chinese men (2018-April 2019). List from FIA investigators.
- **FIA data**: 52 Chinese traffickers arrested in 2019; 31 acquitted in Faisalabad court.

### UNHCR and IOM data
- **UNHCR data portal**: https://data.unhcr.org/en/country/pak — API available. 1.52M registered refugees; 76% women/children.
- **NCHR/UNHCR joint report**: https://nchr.gov.pk/wp-content/uploads/2024/05/Child-Protection-for-Children-on-the-Move-Report.pdf
- **IOM CTDC**: https://www.ctdatacollaborative.org/ — 206,000+ trafficking victims across 190 countries. Downloadable synthetic CSV datasets.
- **IOM protection report 2024**: https://www.iom.int/sites/g/files/tmzbdl2616/files/documents/2026-01/iom-protection-report-2024.pdf — 81,108 migrants returned (13% children).

### UNODC Pakistan
- **Country office**: https://www.unodc.org/copak/
- **TIP MIS launch**: Pakistan launched centralized FIA Trafficking MIS in December 2023 (internal, not public). UNODC identified **31 hotspot districts** for trafficking.
- **Iran border**: FIA operates victim reception center at Taftan, Balochistan. 19,575 migrants from Iran received services.

### Camel jockey historical data
- **Anti-Slavery International**: https://www.antislavery.org/latest/ten-year-olds-forced-risk-lives-racing-camels-uae/ and https://www.antislavery.org/latest/backdated-compensation-ignores-forgotten-child-camel-jockeys/
- **Data**: ~3,000 child jockeys in UAE (2005); 1,100 repatriated (mainly Pakistan); UAE allocated $9M rehabilitation. Source areas: Muzaffargarh, Rahim Yar Khan, Punjab.

---

## Category 10: Social media and Urdu-language platforms

### Roshni Helpline
- **Facebook**: https://www.facebook.com/roshnihelpline/
- **Twitter/X**: https://x.com/Roshni1138
- **Website**: https://roshnihelpline.org/
- **Data**: Missing children posts with photos, names, ages, last-known locations. **13,000+ missing children recovered; 30,000+ families served** since 2003. 4,000+ volunteer network.
- **Scraping feasibility**: MODERATE. Meta Content Library API for authorized researchers. Posts contain structured data (child name, age, location, date missing).

### ZARRA system and Zainab Alert
- **Web portal**: https://zarra.mohr.gov.pk/
- **iOS app**: https://apps.apple.com/us/app/zarra-alert-app/id6472414783
- **Zainab Alert (Invent Lab)**: https://www.zainabalert.com/
- **Data analysis report**: https://mohr.gov.pk/SiteImage/Misc/files/ZARRA%20Data%20Analysis%20Report%20Oct,%202021%20-%20June,%202022.pdf
- **Data**: **3,639 total cases; 2,130 successful closures; 592 ongoing**. District-level breakdowns. SMS alert system within 20km of last-seen location.
- **Scraping feasibility**: LOW for app data. MODERATE for published PDF reports.

### Punjab Safe Cities Authority
- **URL**: https://psca.gop.pk/
- **Data**: Virtual Center for Child Safety (VCCS), "Mera Pyara" missing person campaign, AI facial recognition, **10,000+ CCTV cameras** in Lahore expanding to 6 more cities.
- **Scraping feasibility**: NONE. Government authenticated system. Requires MOU.

### Pakistan Citizen Portal
- **URL**: https://citizenportal.gov.pk/
- **Data**: Zainab Alert integrated since October 2020. 2.9M+ users. Child protection complaints categorized.
- **Scraping feasibility**: VERY LOW. Authenticated, requires CNIC.

### Urdu news portals for automated monitoring
- **Jang**: https://jang.com.pk/ — HIGH scraping feasibility. Keywords: بچوں سے زیادتی, اغوا, گمشدہ بچے
- **Express**: https://express.pk/ — HIGH
- **BBC Urdu**: https://www.bbc.com/urdu — HIGH. RSS feeds available.
- **Geo Urdu**: https://geo.tv/ur/ — HIGH
- **Dawn**: https://www.dawn.com/ — HIGH. Consistently covers child protection.
- **Integration**: Replicate Sahil's 81-newspaper monitoring methodology with automated Urdu NLP scraping.

---

## Category 11: Law enforcement tools and databases

### NCMEC CyberTipline integration architecture
- **URL**: https://report.cybertip.org/
- **Pakistan interface**: NCMEC forwards geographically relevant tips to FIA/NCCIA via secure channel. Reports contain XML/JSON: IP addresses, usernames, URLs, timestamps, file hashes (MD5/SHA1/PhotoDNA), attached files.
- **Integration**: Formal inter-agency agreement. Access via I-24/7 or bilateral channel. Global Platform for Child Exploitation Policy (2024) provides jurisdiction-level analytics.

### ICSE Database (Interpol)
- **URL**: https://www.interpol.int/en/Crimes/Crimes-against-children/International-Child-Sexual-Exploitation-database
- **Pakistan status**: **71st country connected**. 9 FIA officers initially trained. **4.9 million+ images/videos; 42,300+ victims identified globally**.
- **Access**: Via I-24/7 network through NCB Islamabad.

### Project VIC International
- **URL**: https://www.projectvic.org/
- **Hash access**: https://www.projectvic.org/get-hashes
- **VICS data model**: https://www.projectvic.org/vics-data-model
- **Data**: 6 million+ CSAM images/videos discovered. **VICS 2.0 JSON format** standardized across 30+ vendor tools.
- **Pakistan deployment**: No confirmed direct deployment. FIA could access through ICMEC partnership.

### PhotoDNA (Microsoft)
- **URL**: https://www.microsoft.com/en-us/photodna
- **Pakistan deployment**: No confirmed law enforcement deployment. All major platforms operating in Pakistan (Meta, Google, TikTok) use it. **Available free via Azure Cloud Service** for qualified organizations since 2014.
- **Integration**: Microsoft PhotoDNA Cloud Service API (Azure-based, free). Hash sets via NCMEC and IWF.

### Thorn/Spotlight
- **URL**: https://www.thorn.org/ | https://safer.io/
- **Data**: Spotlight used by 8,500+ officers in 2,000 agencies across 35 countries. **14,874 children identified**. Academic paper (PMC/NIH) specifically recommends Spotlight for Pakistan.
- **Pakistan deployment**: None confirmed.

### Griffeye Analyze
- **URL**: https://www.griffeye.com/
- **Data**: **Core version FREE for law enforcement** CSA investigations. Used by 2,500+ agencies in 30+ countries. Imports VICS JSON, PhotoDNA hashes, MD5/SHA1.
- **Pakistan deployment**: None confirmed, but available free.
- **Integration**: FIA/NCCIA requests free license → connects to Project VIC hashes and ICSE database.

### NADRA child registration data
- **URL**: https://www.nadra.gov.pk/child-registration-certificate-crc/
- **Data**: B-Form/CRC for all children under 18. 13-digit unique ID. Biometric data. Parents' CNIC linkage.
- **Scraping feasibility**: NONE. Highly secure. Criminal penalties for unauthorized access.
- **Integration**: Formal MOU for NADRA Verification API (existing, used by banks). B-Form database could cross-reference missing children.

### Virtual Global Taskforce membership
- **URL**: https://www.afp.gov.au/virtual-global-taskforce
- **Pakistan status**: **NOT A MEMBER**. 15 members include AFP, FBI, NCA, Europol, Interpol. Pakistan interfaces indirectly through Interpol.

---

## The 20 highest-priority scrapable sources for immediate integration

The following sources combine the highest data value, best scraping feasibility, and most relevant geographic granularity:

1. **US DOL Pakistan annual report** — Comprehensive, structured PDFs, annual, covers all sectors
2. **Sahil Cruel Numbers** — Best domestic CSA data, annual PDFs, provincial breakdown
3. **NCMEC CyberTipline country data** — Pakistan ranks 3rd globally, annual PDFs
4. **ILOSTAT REST API** — Programmatic CSV access, real-time updates
5. **US TIP Report Pakistan** — Annual, structured HTML, prosecution/conviction data
6. **US DOL TVPRA List** — Machine-readable Excel, biennial
7. **DHS API** — JSON access, provincial child marriage data
8. **UNICEF SDMX API** — Structured child protection indicators
9. **JPP data portal** — Open-source juvenile justice data
10. **SPARC/stateofchildren.com** — Structured HTML data tables
11. **ECPAT country page + PDFs** — Comprehensive assessments
12. **Provincial child labour surveys (Punjab/Sindh/KP)** — District-level PDFs
13. **Zenodo brick kiln GPS dataset** — Open CSV/GeoJSON
14. **CSJ Pakistan forced conversion data** — Annual PDFs with case data
15. **NCRC State of Children Report** — First national comprehensive assessment
16. **Meta Transparency Reports** — CSV downloads, quarterly
17. **Google Transparency Report** — Pakistan filter, data export
18. **DRF monthly newsletters** — Helpline statistics
19. **IOM CTDC synthetic dataset** — Downloadable CSV
20. **UNHCR data portal API** — Monthly refugee/child data updates

---

## Critical data gaps and integration architecture

Five systemic gaps define Pakistan's child protection data landscape. First, **no unified national missing children database** exists — ZARRA, Roshni Helpline, PSCA Mera Pyara, and police systems operate in parallel without data sharing. Second, **Pakistan has no INHOPE member hotline**, leaving CSAM reporting dependent on the IWF/DRF portal. Third, **no confirmed deployments of PhotoDNA, Thorn Spotlight, Project VIC, or Griffeye** exist within Pakistani law enforcement, despite all being available free to qualifying agencies. Fourth, **government databases (NADRA B-Forms, KP CPIMS, Punjab PMIS, FIA TIP MIS) are entirely internal** with no public APIs — every one requires a formal MOU. Fifth, **PBS crime statistics do not disaggregate by juvenile age**, making NGO sources (Sahil, SPARC, JPP) the only alternatives.

The recommended integration architecture flows through four layers. The **ingestion layer** deploys web scrapers with Urdu NLP for newspaper monitoring (replicating Sahil's 81-paper methodology), API connectors for ILOSTAT/DHS/UNICEF/UNHCR structured data, PDF extraction pipelines for annual reports, and secure channels for NCMEC CyberTipline and Interpol ICSE feeds. The **processing layer** runs Urdu named-entity recognition for location/person extraction, PhotoDNA hash matching for image deduplication, VICS 2.0 JSON processing for forensic tool interoperability, and a deduplication engine cross-referencing children across multiple reporting sources. **Storage** uses PostgreSQL for structured case data, Elasticsearch for full-text Urdu search, PostGIS for geospatial brick kiln and district boundary data, and S3 for document/image storage. The **intelligence layer** produces district-level heat maps across all 11 exploitation categories, a missing children cross-reference engine (ZARRA × NADRA × Roshni × Sahil × PSCA), trend analysis combining Sahil newspaper data with social media signals, and automated alert generation for emerging cases.

The key protocols enabling this architecture are REST APIs (JSON) for international databases, VICS 2.0 JSON for forensic hash sharing, SDMX for UNICEF statistical data, and Interpol I-24/7 for secure law enforcement channels. Every one of the 145+ sources documented above can feed into this pipeline — the difference lies only in whether access is open (scraped immediately), gated (requiring free registration), or restricted (requiring government MOUs that the Nigehbaan team must pursue in parallel with technical development).