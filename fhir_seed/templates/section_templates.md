# Section templates for document bundles

Maximum versions of the narrative `div` for the Composition header and the
seven sections of a discharge summary. Copy a block, delete what you do not
need, fill in the rest, and paste it into the matching `div` string in
`fhir_seed/data/document_bundle_final/*.json` (search terms: `TODO header`
and `"title": "<section title>"`).

Every placeholder starts with `TODO`

Rules for pasting into JSON:

- Use single quotes for attributes (`xmlns='...'`), never double quotes.
- Write `&amp;` for `&` and `&lt;` for `<` in text.
- Only these elements are used here: `div`, `p`, `br`, `b`, `i`, `ul`, `ol`,
  `li`, `table`, `caption`, `thead`, `tbody`, `tr`, `th`, `td`. Section
  headings come from `section.title`, so do not repeat them inside.

## Composition header (`Composition.text.div`, search `TODO header`)

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <p><b>TODO hospital name</b><br/>TODO street, TODO postal code TODO city<br/>Phone: TODO phone</p>
  <p><b>Discharge summary</b></p>
  <table>
    <tbody>
      <tr><th>Patient</th><td>TODO name</td></tr>
      <tr><th>Date of birth</th><td>TODO date</td></tr>
      <tr><th>Sex</th><td>TODO sex</td></tr>
      <tr><th>Address</th><td>TODO address</td></tr>
      <tr><th>Admission</th><td>TODO date</td></tr>
      <tr><th>Discharge</th><td>TODO date</td></tr>
      <tr><th>Department</th><td>TODO department</td></tr>
      <tr><th>Attending physician</th><td>TODO name</td></tr>
      <tr><th>Date of letter</th><td>TODO date</td></tr>
    </tbody>
  </table>
</div>
```

## Reason for admission

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <p>TODO name, a TODO age-year-old TODO man/woman, was admitted on TODO date to TODO department because of TODO reason.</p>
  <p>Relevant history: TODO pre-existing conditions and previous treatment.</p>
  <p>Findings on admission: TODO complaints, examination, vital signs.</p>
  <p>Allergies: TODO allergies or none known.</p>
</div>
```

## Diagnoses

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <p><b>Principal diagnosis</b></p>
  <ul>
    <li>TODO diagnosis</li>
  </ul>
  <p><b>Secondary diagnoses</b></p>
  <ul>
    <li>TODO diagnosis</li>
    <li>TODO diagnosis</li>
  </ul>
  <p><b>Pre-existing conditions</b></p>
  <ul>
    <li>TODO condition</li>
  </ul>
</div>
```

## Hospital course

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <p>TODO summary of the course: findings, investigations, treatment, complications.</p>
  <table>
    <caption>Timeline</caption>
    <thead>
      <tr><th>Date</th><th>Event</th></tr>
    </thead>
    <tbody>
      <tr><td>TODO date</td><td>TODO event</td></tr>
      <tr><td>TODO date</td><td>TODO event</td></tr>
    </tbody>
  </table>
  <p>Treatment during the stay: TODO inpatient medication and therapies.</p>
  <p>Condition at discharge: TODO.</p>
</div>
```

## Results

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <p>TODO short assessment of the findings.</p>
  <table>
    <caption>Laboratory results</caption>
    <thead>
      <tr><th>Test</th><th>On admission (TODO date)</th><th>Before discharge (TODO date)</th><th>Unit</th><th>Reference range</th></tr>
    </thead>
    <tbody>
      <tr><td>TODO test</td><td>TODO value</td><td>TODO value</td><td>TODO unit</td><td>TODO range</td></tr>
      <tr><td>TODO test</td><td>TODO value</td><td>TODO value</td><td>TODO unit</td><td>TODO range</td></tr>
    </tbody>
  </table>
  <p>Further findings (imaging, ECG, microbiology): TODO or none.</p>
</div>
```

## Medications at discharge

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <table>
    <thead>
      <tr><th>Medication</th><th>Dose</th><th>Frequency</th><th>Route</th><th>Comment</th></tr>
    </thead>
    <tbody>
      <tr><td>TODO medication</td><td>TODO dose</td><td>TODO frequency</td><td>TODO route</td><td>TODO comment</td></tr>
      <tr><td>TODO medication</td><td>TODO dose</td><td>TODO frequency</td><td>TODO route</td><td>TODO comment</td></tr>
    </tbody>
  </table>
  <p>Stopped or changed during the stay: TODO or none.</p>
</div>
```

## Procedures

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <table>
    <thead>
      <tr><th>Date</th><th>Procedure</th><th>Details</th></tr>
    </thead>
    <tbody>
      <tr><td>TODO date</td><td>TODO procedure</td><td>TODO details</td></tr>
      <tr><td>TODO date</td><td>TODO procedure</td><td>TODO details</td></tr>
    </tbody>
  </table>
  <p>Complications: TODO or none.</p>
</div>
```

## Follow-up

```html
<div xmlns='http://www.w3.org/1999/xhtml'>
  <p><b>Recommendations</b></p>
  <ul>
    <li>TODO follow-up appointment: with whom, when</li>
    <li>TODO laboratory controls</li>
    <li>TODO medication adjustments</li>
  </ul>
  <p>Appointments: TODO or none arranged.</p>
  <p>Kind regards,<br/>TODO physician name<br/>TODO department, TODO hospital</p>
</div>
```