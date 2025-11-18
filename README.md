<div align="center">

# EDIT-Bench: Evaluating LLM Abilities to Perform Real-World Instructed Code Edits

_EDIT-Bench is a code editing benchmark built on real code edits gathered from VSCode._
<p align="center">
  <a href="https://arxiv.org/abs/2511.04486">
    <img src="https://img.shields.io/badge/%F0%9F%93%84%20arXiv-2511.04486-b31b1b?style=for-the-badge" alt="arXiv Paper"/>
  </a>
  &nbsp;
  <a href="https://huggingface.co/datasets/copilot-arena/EditBench">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Dataset-Hugging%20Face-ffc107?style=for-the-badge" alt="Dataset on Hugging Face"/>
  </a>
  &nbsp;
  <a href="https://waynechi.com/edit-bench/">
    <img src="https://img.shields.io/badge/%F0%9F%8F%86%20Leaderboard-Website-1f8ef1?style=for-the-badge" alt="Leaderboard Website"/>
  </a>
</p>

[![GitHub stars](https://img.shields.io/github/stars/waynchi/editbench?style=flat-square&logo=github)](https://github.com/waynchi/editbench)
[![GitHub forks](https://img.shields.io/github/forks/waynchi/editbench?style=flat-square&logo=github)](https://github.com/waynchi/editbench)
[![GitHub last commit](https://img.shields.io/github/last-commit/waynchi/editbench?style=flat-square&logo=github)](https://github.com/waynchi/editbench)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=flat-square)](https://www.python.org/downloads/)

</div>

---

> **Quick Links**  
> 📄 **Paper:** [arXiv 2511.04486](https://arxiv.org/abs/2511.04486)  
> 📦 **Dataset:** [Hugging Face /copilot-arena/EDIT-Bench](https://huggingface.co/datasets/copilot-arena/EditBench)  
> 🏆 **Leaderboard:** [waynechi.com/edit-bench](https://waynechi.com/edit-bench/)


## Quick Start

Evaluating new models on EDIT-Bench is easy!

1. Install Docker.
2. Provide your generated code edits.
3. Modify and run the script at `examples/run_experiment.py`

### Example
As an example, we pre-generated code edits for `gpt-o3-mini`.
Generations with the expected format are found at `generations/whole_file/gpt-o3-mini`.

To evaluate these generations:

```bash
bash run_experiment.sh examples/run_experiment.py
```
You will find the results in `example_results/gpt-o3-mini.json`


## Customize Experiments

The core function used to run our experiments is:

```python
test_edits(gen_path=GENERATION_PATH, split=SPLIT, output_file=OUTPUT_FILE)
```

We provided the simplest example with `run_experiments.py`, however you can customize the file in multiple ways.

### Generation Example

You need to generate files before running our tests. We've provided an example at `examples/generate_and_run_experiment.py` on how to do both at once.

```bash
bash run_experiment.sh examples/generate_and_run_experiment.py
```

This uses the `prompts/whole_file.txt` prompt which is the baseline used in our paper.

### Other Examples

For a complete end-to-end generation and testing script using OpenRouter and OpenAI, see `examples/openrouter_experiment.py` and `examples/openai_experiment.py`. These scripts take a YAML file as the first argument and runs the experiment with the configuration inside the YAML. For example:
```bash
bash run_experiment.sh examples/openai_experiment.py configs/gpt-5-high.yaml
```
To view experiments, use the `scripts/display_results_csv.py` script provided by passing in the directory containing your results:
```bash
python3 scripts/display_results_csv.py <path_to_json_dir>
```
Many optional arguments are provided to change the formatting and information (e.g. `--csv` flag returns the data in csv form, `--split` partitions data to specific questions in the split)

## Extra Information

All experiments are executed using the `run_experiment.sh` shell script, which serves as the main command-line interface for the framework. 
This script handles building docker containers and running experiments inside the container.
All environment variables to be used in the docker container are defined in the `EditBench.config` file.

### Commands in run_experiment

By default, the bash script will built and run the docker container, then execute the given python file along with the command line arguments inside the docker container. 
```bash
bash ./run_experiment <path to python file> [args for python file]
```

To help with debugging, we provide the `build` and `shell` commands
```
# Force rebuild the Docker container
bash ./run_experiment build

# Create an interactive session (useful for debugging)
bash ./run_experiment shell
```

<details>
<summary><b>Writing Your Own Inference & Testing Script</b></summary>

Experiments run inside Docker containers, and the `edit_bench` package provides convenient functions for running experiments. The docker container is an isolated execution environment and mounts this repo inside the container as `/projects` (can be accessed using the WORKDIR env variable). Edits made in this repo are synced with the repo inside docker.

The two function you need from `edit_bench.evaluation` are:

- **`generate_files`** - Generates code files for the specified model
- **`test_edits`** - Runs tests for the specified model's generations

The end-to-end examples (e.g. `examples/openai_experiment.py`) provide practical uses for these function. The spec for these functions:

`generate_files(fn, prompt_path, generations_path, split)`
- This function loads data from HF and uses `fn` in multiple threads to generate solutions to each problem. The function ignores problem_ids that already exist in `generations_path`
- `fn(prompt, lang)` is a function that takes a prompt string and programming language string and returns the model's generation for that prompt. The lang string makes parsing the output easier
- `prompt_path` is the path to the prompt f-string. See `prompts/` for examples. The f-string has access to variables: lang (programming language), original_code, instruction (user instruction), and highlighted_code
- `generation_path` is the directory for generated outputs. The generations are stored by problem_id name. Set the path prefix to  `/projects` (can be accessed using the WORKDIR env variable) for the generations to persist outside of docker.
- `split` the set of questions to use from HF

`test_edits(gen_path, split, output_file)`
- This function tests the generations in the `gen_path` directory and returns the results (as json) to `output_file`. The tests will not run if > 90% of results are already present in the output file (strongly indicates that tests were already run).
- `gen_path` where the generations are located
- `split` the HF split to use
- `output_file` the location of outputs. Use `/projects` (can be accessed using the WORKDIR env variable) to ensure results persists between docker runs.

</details>

## Contact

For questions and feedback, please open an issue or feel free to reach out directly!

### Authors

<table>
<tr>
    <td align="center">
        <a href="https://waynechi.com">
            <img src="https://github.com/waynchi.png" width="100px;" alt="Wayne Chi"/>
            <br />
            <sub><b>Wayne Chi</b></sub>
        </a>
        <br />
        <a href="https://twitter.com/iamwaynechi">Twitter</a> •
        <a href="https://github.com/waynchi">GitHub</a> •
        <a href="https://waynechi.com">Website</a>
    </td>
    <td align="center">
        <a href="https://valeriechen.github.io">
            <img src="https://github.com/valeriechen.png" width="100px;" alt="Valerie Chen"/>
            <br />
            <sub><b>Valerie Chen</b></sub>
        </a>
        <br />
        <a href="https://twitter.com/valeriechen_">Twitter</a> •
        <a href="https://github.com/valeriechen">GitHub</a> •
        <a href="https://valeriechen.github.io">Website</a>
    </td>
    <td align="center">
        <a href="https://rShar01.github.io">
            <img src="https://github.com/rShar01.png" width="100px;" alt="Ryan Shar"/>
            <br />
            <sub><b>Ryan Shar</b></sub>
        </a>
        <br />
        <a href="https://twitter.com/RyanShar01">Twitter</a> •
        <a href="https://github.com/rShar01">GitHub</a> •
        <a href="https://rShar01.github.io">Website</a>
    </td>
</tr>
</table>

## License

This project is licensed under the Apache 2.0 License.

## Citation

```bibtex
@misc{chi2025editbenchevaluatingllmabilities,
      title={EDIT-Bench: Evaluating LLM Abilities to Perform Real-World Instructed Code Edits}, 
      author={Wayne Chi and Valerie Chen and Ryan Shar and Aditya Mittal and Jenny Liang and Wei-Lin Chiang and Anastasios Nikolas Angelopoulos and Ion Stoica and Graham Neubig and Ameet Talwalkar and Chris Donahue},
      year={2025},
      eprint={2511.04486},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2511.04486}, 
}
```
