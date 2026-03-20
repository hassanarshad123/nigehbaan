"""Tests for the court judgment PDF parser."""


from data.parsers.court_judgment_parser import CourtJudgmentParser


class TestCourtJudgmentParser:
    def test_extract_ppc_sections(self):
        parser = CourtJudgmentParser()
        text = "The accused was charged under section 370 and u/s 371-A PPC"
        sections = parser.extract_ppc_sections(text)
        assert "370" in sections
        assert "371-A" in sections

    def test_extract_ppc_sections_various_formats(self):
        parser = CourtJudgmentParser()
        text = "Sec. 366-A, S. 377, under section 292-A of PPC"
        sections = parser.extract_ppc_sections(text)
        assert "366-A" in sections
        assert "377" in sections
        assert "292-A" in sections

    def test_extract_case_header(self):
        parser = CourtJudgmentParser()
        text = "IN THE SUPREME COURT OF PAKISTAN\nCr.A. No. 123/2024\nDate: 15-01-2024"
        header = parser.extract_case_header(text)
        assert header.get("case_number") == "Cr.A. No. 123/2024"
        assert header.get("court") == "Supreme Court of Pakistan"

    def test_extract_parties(self):
        parser = CourtJudgmentParser()
        text = "Muhammad Ali vs State\nPetitioner: Muhammad Ali\nRespondent: The State"
        parties = parser.extract_parties(text)
        assert "petitioner" in parties or "respondent" in parties

    def test_extract_victim_demographics_age(self):
        parser = CourtJudgmentParser()
        text = "The victim, a minor girl aged 12 years, was recovered from"
        demographics = parser.extract_victim_demographics(text)
        assert demographics.get("victim_age") == 12
        assert demographics.get("victim_gender") == "female"

    def test_extract_sentence(self):
        parser = CourtJudgmentParser()
        text = "The accused was sentenced to 10 years rigorous imprisonment and fine of Rs. 50,000."
        sentence = parser.extract_sentence(text)
        assert sentence is not None
        assert "10 years" in sentence or "rigorous" in sentence.lower()

    def test_extract_sentence_acquittal(self):
        parser = CourtJudgmentParser()
        text = "The appeal is allowed and the accused is acquitted of all charges."
        sentence = parser.extract_sentence(text)
        assert sentence is not None
        assert "acquitted" in sentence.lower() or "allowed" in sentence.lower()

    def test_extract_district(self):
        parser = CourtJudgmentParser()
        text = "FIR No. 123/2024 registered at P.S. Saddar, District Lahore"
        district = parser.extract_district(text)
        assert district is not None
        assert "Lahore" in district or "lahore" in district.lower()
