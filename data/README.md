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

| Prompt Key in Code                | Description as in the paper          | Short name in the paper's main text | Short name in Tables |
|-----------------------------------|--------------------------------------|-------------------------------------|----------------------|
| `prompt_v1_ta_min`                | Task Agnostic                        | Task-Agnostic| Task Agn.
| `prompt_v3_ts_ext_rubric`         | Instruction + Rubric                 | Instr.+Rubric| Ins.+Rub.
| `prompt_v4_ts_ext_model`          | Instruction + Solution               | Instr.+Solution| Ins.+Sol.
| `prompt_v5_ts_ext_rubric_model`   | Instruction + Rubric + Solution      | Instr.+Rubric+Solution| Ins.+Rub.+Sol.


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

