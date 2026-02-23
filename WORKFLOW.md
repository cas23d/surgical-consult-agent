# Clinical Workflow Reference

Source: Christopher Stephenson, MD — real surgical consult workflow

## Entry Point

Surgeon receives consult page with:
- Patient identifiers (MRN)
- Free-text message (reason for consult + whatever context sender included)

## Triage Pass: "Sick or Not Sick"

- Location: ICU vs floor vs ED
- Vitals / instability: tachycardia, hypotension, pressor requirement
- Imaging (often CT): radiology reads can mismatch reality
- Labs: overall severity / physiologic derangement

## Treatment Context: What's Already Happening

- Meds/orders: pressors? antibiotics? fluids?
- Ins & outs: NG tube? fluid received? last BM, vomiting?

## Deeper Story-Building

- Notes tab: hospital course, length of stay
- Past history, prior surgeries (especially at this institution)
- Surgical candidacy (medical + patient preference/values)
- Then: go see the patient

## Desired Outputs

1. Red flags highlighted (things I shouldn't miss)
2. Missing information flagged + prompts for what to ask the patient
3. Evidence-based management plan from chart data
   - Must cite specific guideline and source
   - Recognize guidelines may not apply cleanly (e.g., SBO + Roux-en-Y)
4. Suggested additional workup (imaging, labs, consultants)
5. Draft consult note
6. Staffing summary (help sounding coherent on hour 28)
