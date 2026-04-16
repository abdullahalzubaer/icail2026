## `./instructor_material_public_law`
Contains the instructor materials for the public law part of the study, including:
- the case facts,
- the correction guideline given to the human graders,
- grading rubrics, and
- sample solutions.

## `./model_grades`
Contains all grades produced by the model across all of our experiments.


### Prompt Mapping

The column of the csv file has the following aliases in the code and they correspond to the descriptions in the paper as follows:

| Prompt Key in Code                | Description as in the paper          |
|-----------------------------------|--------------------------------------|
| `prompt_v1_ta_min`                | Task Agnostic                        |
| `prompt_v3_ts_ext_rubric`         | Instruction + Rubric                 |
| `prompt_v4_ts_ext_model`          | Instruction + Solution               |
| `prompt_v5_ts_ext_rubric_model`   | Instruction + Rubric + Solution      |


General structure of one prompt column is as follows:


`{backend}_{prompt_key}_{ha_or_dp}__{model_id}__i{run_index}__{hash}__extracted_element`


Where:

- `{backend}`: inference backend used to run the model (e.g., `litellm`, `vllm`)
- `{prompt_key}`: one of  
  `prompt_v1_ta_min`, `prompt_v3_ts_ext_rubric`, `prompt_v4_ts_ext_model`, `prompt_v5_ts_ext_rubric_model`
- `{ha_or_dp}`: dataset ( ha->`criminal_law` or dp->`public_law`)
- `{model_id}`: exact model identifier used in the run (e.g., `gpt-5-2025-08-07`)
- `{run_index}`: run / repetition index (e.g., `i1`, `i2`, `i3`)
- `{hash}`: unique run hash for traceability used internally (e.g., `h44136fa3`)

Example (format illustration):

`litellm_prompt_v1_ta_min_ha__gpt-5-2025-08-07__i2__h44136fa3__extracted_element`

`vllm_prompt_v5_ts_ext_rubric_model_ha__eurollm-22b-instruct-2512__i1__h44136fa3__extracted_element`


---

**Caption:** Summarized case facts and student tasks for criminal and public law; translated to English from German.

| Case fact | Student task |
|---|---|
| **Criminal Law:** A altered an inspection sticker, obstructed an overtaking driver who crashed while avoiding collision, and left; she also induced her sister to falsely accept responsibility for a speeding offense, and arranged an inaccurate alibi at trial, leading to A's conviction. The police later searched the sister's empty apartment based on a prosecutor's (not a judge's) order after detecting marijuana odor, found narcotics; the admissibility of that evidence is disputed. | Part I: Determine the criminal liability of A, her sister, and her friend. Part II: Analyze the admissibility of the narcotics evidence and whether an objection is required for any exclusion. |
| **Public Law:** A city enacted and published a pigeon-feeding ban that was adopted by the council despite not being on the council's meeting agenda. After a resident kept feeding pigeons, the city issued an individual enforcement order; he timely sued to annul it, alleging defects in the ordinance's adoption and legal basis. | Assess the likelihood of success of the annulment action against the individual order, including incidental review of the underlying ordinance's validity. |
