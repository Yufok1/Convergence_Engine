---
title: Convergence Engine Private
emoji: ðŸ§ª
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

Convergence Engine Quick Reference
==================================

Range of ranges
---------------

Color is signal, not decoration. Each band names the kind of attention a section needs, and every color has a word beside it so meaning never depends on hue alone.

This guide assumes the reader is an intelligent being. Its job is to make the machine legible, not make the reader small.

The color array is not a test. It does not grade vision. It does not tell anyone what they can or cannot perceive. If color is absent, reduced, shifted, or unwanted, the words still carry the whole instruction.

The band label is not a directive. It names the kind of live condition that has appeared. When the problem shows itself, the band helps you see what class of attention it needs.

![Spectrum range check](assets/spectrum/range-check.svg)

If two bands look identical, if one band disappears, or if a boundary is hard to see, that is a range cutoff signal. Plain-language version: you may be color-blind across that range. That is not shame and not exclusion. Use the written band name and function. The path remains open.

![Violet](assets/spectrum/violet.svg) **Violet / threshold:** gates, custody, entry, handoff.

![Blue](assets/spectrum/blue.svg) **Blue / orientation:** where you are, what to read, what to check.

![Green](assets/spectrum/green.svg) **Green / action:** commands that build, run, or move the system forward.

![Gold](assets/spectrum/gold.svg) **Gold / optional range:** useful branches, not required for the main path.

![Red](assets/spectrum/red.svg) **Red / repair:** stop, interpret the error, recover without panic.

![White](assets/spectrum/white.svg) **White / receipt:** memory, proof, notes, and durable state.

Cheat code
----------

![Violet](assets/spectrum/violet.svg) **Violet / threshold:** this is the smallest gate, not a wall.

```text
techlady
```

If JupyterLab asks for a password, type `techlady`. That is the whole door: no paywall, no maze.

How to use this sheet
---------------------

![Blue](assets/spectrum/blue.svg) **Blue / orientation:** one box, one action, then wait for the machine to answer.

Copy one command box. Paste it into the JupyterLab Terminal. Press Enter. Wait until the prompt comes back, then copy the next command box.

Do not paste two boxes at once. Do not copy the terminal prompt. If the terminal shows `#`, that is the prompt, not part of the command.

The rhythm is simple:

1. copy one command box
2. paste it
3. press Enter
4. wait until the prompt comes back
5. read the answer before the next box

Prompt signs:

```text
#
```

means the terminal is ready.

```text
(.venv) #
```

means the engine Python environment is active and the terminal is ready.

If two commands get pasted by accident, pause and read the result. You are not in trouble. If the prompt says `(.venv) #`, the environment is active. Continue from the next single command.

Code wheel
----------

![Violet](assets/spectrum/violet.svg) **Violet / rotation:** one active code, reserve codes held in view.

Only one code is active at a time. The current code is the one to try first.

```text
techlady
```

Reserve codes:

```text
techlit
crayonlab
gamegenie
wordfood
tinydoor
livinglab
organismgarden
cocooncode
jupyterjoy
```

Entry is right there. It only asks for one small sign that you read the door.

Accessibility notes
-------------------

![White](assets/spectrum/white.svg) **White / full spectrum:** perception is plural, so no instruction depends on color alone.

Plain text. One command per box. No combined commands. No color-only meaning. Short headings for screen readers. Optional steps say optional.

Brotology rule
--------------

![Magenta](assets/spectrum/magenta.svg) **Magenta / relation:** humor is allowed to soften the door; truth still carries the weight.

The name is a joke. The method is not. Be funny. Be honest. Read the room before you touch the machine.

The banger raid order is:

1. get status
2. get sitrep
3. poke one thing
4. watch what changed

Use these when you are unsure:

```bash
python cra_cli.py status
```

```bash
python cra_cli.py sitrep
```

JupyterLab front door
---------------------

![Blue](assets/spectrum/blue.svg) **Blue / front door:** this is the live room where the work happens.

This Space uses the `JUPYTER_TOKEN` secret as the Jupyter password. Set the Space secret to:

```text
JUPYTER_TOKEN=techlady
```

The mounted bucket belongs at `/data`. JupyterLab opens in `/data/work`. Clone the repo there so `Convergence_Engine/data` lives on the bucket. Keep Python virtual environments off `/data`; the bucket is for durable engine data, not thousands of tiny package files.

Open a Terminal inside JupyterLab and run the boxes below one at a time.

Clone the engine
----------------

![Green](assets/spectrum/green.svg) **Green / materialize:** bring the engine into the bucket-backed workspace.

Run:

```bash
cd /data/work
```

Run:

```bash
git clone https://github.com/Yufok1/Convergence_Engine.git /data/work/Convergence_Engine
```

If it says `destination path 'Convergence_Engine' already exists`, that is okay. ![Red](assets/spectrum/red.svg) **Red / repair:** the clone already happened. Do not clone again. Do not delete the folder. Run the next box.

Plain version: `fatal` is Git yelling, not the engine dying. The folder is already there.

Run:

```bash
cd /data/work/Convergence_Engine
```

If you are updating an existing clone, run this only after the `cd` above:

```bash
git pull
```

Do not run `git pull` from `/data/work`. Git pull only works from inside the repo.

This absolute path works even when the terminal starts somewhere surprising. If it says `can't cd to /data/work/Convergence_Engine`, the clone did not finish. ![Red](assets/spectrum/red.svg) **Red / repair:** check location before repeating commands:

```bash
pwd
```

If the path ends with `Convergence_Engine`, keep going.

Prepare the bucket data room
----------------------------

![Green](assets/spectrum/green.svg) **Green / bucket room:** make the durable engine data room before any builder writes into it.

Run:

```bash
mkdir -p data
```

Run:

```bash
cp config.json data/config.json
```

Plain version: `/data` is the Hugging Face bucket. `/data/work/Convergence_Engine/data` is the engine's durable data room inside that bucket.

Make the Python environment
---------------------------

![Green](assets/spectrum/green.svg) **Green / tool body:** make the local Python room the engine can live inside.

The repo is on `/data`. The virtualenv is not. This avoids bucket input/output errors while Python imports packages.

Run:

```bash
/usr/local/bin/python -m venv /home/user/.venvs/convergence-engine
```

If it says `ensurepip` failed, do not activate a half-built environment. Use the repair card below.

Do not make this environment inside `/data/work/Convergence_Engine/.venv`. The bucket can be slow or fussy with thousands of tiny package files. Put the Python room in `/home/user/.venvs/convergence-engine` and let the engine data stay on `/data`.

Run:

```bash
. /home/user/.venvs/convergence-engine/bin/activate
```

There is a space between the first dot and `/home`. ![Red](assets/spectrum/red.svg) **Red / repair:** `/usr/bin/sh` uses the dot command. If you see `source: not found`, use this dot command instead.

Bucket venv repair
------------------

![Red](assets/spectrum/red.svg) **Red / repair:** use this if you already created `.venv` inside `/data/work/Convergence_Engine`.

Run:

```bash
deactivate
```

If it says `deactivate: not found`, that is okay. Keep going.

Run:

```bash
cd /data/work/Convergence_Engine
```

Run:

```bash
/usr/local/bin/python -m venv /home/user/.venvs/convergence-engine
```

Run:

```bash
. /home/user/.venvs/convergence-engine/bin/activate
```

Do not use `/data/work/Convergence_Engine/.venv`. That old folder can sit there unused.

Exact error cards
-----------------

![Red](assets/spectrum/red.svg) **Red / repair:** match the words on screen, then take the smallest next step.

If you see:

```text
fatal: destination path 'Convergence_Engine' already exists and is not an empty directory.
```

Run:

```bash
cd /data/work/Convergence_Engine
```

If you see:

```text
source: not found
```

Run:

```bash
. /home/user/.venvs/convergence-engine/bin/activate
```

If you see:

```text
ensurepip returned non-zero exit status 1
```

Run:

```bash
/usr/local/bin/python -m venv /home/user/.venvs/convergence-engine
```

If you see:

```text
OSError: [Errno 5] Input/output error
```

That usually means the bucket-backed environment got weird while Python was importing packages. Use the off-bucket environment, reinstall packages, and keep going:

```bash
. /home/user/.venvs/convergence-engine/bin/activate
```

```bash
python -m pip install --no-cache-dir -r requirements.txt
```

Then retry the command that failed.
If you see:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'data/butterfly_vocabulary_200k_raw.json'
```

The vocabulary builder is trying to write into `data/`, but the room does not exist yet. Make it, then rerun the builder:

```bash
mkdir -p data
```

```bash
python build_curated_dataset.py
```

If you see:

```text
Explorer initialization failed: [Errno 2] No such file or directory: 'data/config.json'
```

The main engine can read `config.json`, but Explorer/Sentinel expects a runtime copy inside `data/config.json`. Copy the map into the runtime room:

```bash
cp config.json data/config.json
```

Then rerun:

```bash
python unified_entry.py --config config.json --no-viz --debug
```

If setup says:

```text
Symlinked ./data -> /dev/shm/convergence_data
```

you are on an older engine checkout or an older guide path. That message means the engine moved `data/` to fast RAM storage instead of keeping it on the Hugging Face bucket.

Repair it for the current run:

```bash
cp config.json data/config.json
```

Then continue.

The patched engine keeps `./data` on `/data` when the repo is under `/data/work/Convergence_Engine`.

Upgrade pip
-----------

![Green](assets/spectrum/green.svg) **Green / prepare:** update the installer before asking it to carry the engine.

Run:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install the engine parts
------------------------

![Green](assets/spectrum/green.svg) **Green / assemble:** install the declared pieces from the repo.

Run:

```bash
python -m pip install --no-cache-dir -r requirements.txt
```

Set WordNet storage
-------------------

![Green](assets/spectrum/green.svg) **Green / language food cache:** store NLTK corpus data on the bucket, not inside the virtualenv.

Run:

```bash
mkdir -p /data/nltk_data
```

Run:

```bash
export NLTK_DATA=/data/nltk_data
```

Run:

```bash
python -m nltk.downloader -d /data/nltk_data wordnet omw-1.4
```

Check imports
-------------

![Gold](assets/spectrum/gold.svg) **Gold / verification:** prove Python can read the installed packages before building the vocabulary.

Run:

```bash
python -c "import numpy, nltk; print('numpy', numpy.__version__); print('nltk', nltk.__version__)"
```

Check setup
-----------

![Gold](assets/spectrum/gold.svg) **Gold / verification:** ask the repo what is missing before guessing.

Run:

```bash
python check_setup.py
```

Build the language food
-----------------------

![Green](assets/spectrum/green.svg) **Green / growth:** feed the vocabulary and knowledge substrate before expecting life.

Run:

```bash
mkdir -p data
```

Run:

```bash
cp config.json data/config.json
```

Run:

```bash
python build_curated_dataset.py
```

Run:

```bash
python merge_nuclear_vocab.py
```

Run:

```bash
python generate_innate_vocab.py
```

Start with a check
------------------

![Gold](assets/spectrum/gold.svg) **Gold / preflight:** test the launch path without committing to a live run.

Run:

```bash
mkdir -p data
```

Run:

```bash
cp config.json data/config.json
```

Run:

```bash
python unified_entry.py --config config.json --check-only --no-viz
```

Start the world
---------------

![Green](assets/spectrum/green.svg) **Green / live run:** start the engine and let the process keep breathing.

Run:

```bash
python unified_entry.py --config config.json --no-viz --debug
```

This command keeps running. ![Blue](assets/spectrum/blue.svg) **Blue / orientation:** a quiet prompt is expected while the world is running. Leave that terminal alone and open a new Terminal for status commands.

Open the web view
-----------------

![Cyan](assets/spectrum/cyan.svg) **Cyan / transport:** local addresses are inside the Space unless a tunnel exposes them.

Inside the Space, the web UI listens here:

```text
http://localhost:5000
```

That is inside the Space container. Your browser cannot always open it directly. Use the tunnel section if you need a public browser URL.

Useful status commands
----------------------

![Blue](assets/spectrum/blue.svg) **Blue / observation:** read the organism state before touching it.

Run one box at a time:

```bash
python cra_cli.py status
```

```bash
python cra_cli.py sitrep
```

```bash
python cra_cli.py training-status
```

```bash
python cra_cli.py exporter-status
```

```bash
python cra_cli.py organisms --limit 10
```

```bash
python cra_cli.py alliances
```

Useful dashboard commands
-------------------------

![Cyan](assets/spectrum/cyan.svg) **Cyan / sightlines:** open a second view without disturbing the running world.

Open another terminal. Activate the engine virtualenv again. Then run one box at a time:

```bash
. /home/user/.venvs/convergence-engine/bin/activate
```

```bash
python live_dashboard.py
```

```bash
python causation_web_ui.py
```

Talk and poke
-------------

![Magenta](assets/spectrum/magenta.svg) **Magenta / contact:** speak to the system without pretending the poke is the whole truth.

Run one box at a time:

```bash
python cra_cli.py repl --model llama3.2
```

```bash
python cra_cli.py standin-chat "cooperate" --max-organisms 1
```

```bash
python cra_cli.py butterfly-chat "cooperate" --max-organisms 1
```

Do not run this until you replace `REPLACE_WITH_ORGANISM_ID`. ![Red](assets/spectrum/red.svg) **Red / repair:** placeholder text is not an organism.

```bash
python cra_cli.py organism-chat REPLACE_WITH_ORGANISM_ID "cooperate"
```

Tune one small thing
--------------------

![Gold](assets/spectrum/gold.svg) **Gold / controlled change:** change one knob, then observe what moved.

Run:

```bash
python cra_cli.py config-set /simulation/max_frames 5000
```

Write a science note
--------------------

![White](assets/spectrum/white.svg) **White / receipt:** leave evidence for the next mind that enters the room.

Run one box at a time:

```bash
python cra_cli.py notepad --summary
```

```bash
python cra_cli.py notepad-add observation "Run started #baseline"
```

```bash
python cra_cli.py scientific-receipt --title "Baseline run receipt"
```

Optional public tunnel
----------------------

![Gold](assets/spectrum/gold.svg) **Gold / optional transport:** only expose a public path when you actually need one.

Only use this if you need a public URL for the web UI. The Space already has SSH installed. Do not run `sudo`.

The web UI must be running before the tunnel can serve anything. Open a second terminal, activate the venv, and start the web UI first:

```bash
. /home/user/.venvs/convergence-engine/bin/activate
```

```bash
cd /data/work/Convergence_Engine
```

```bash
python causation_web_ui.py
```

Wait until you see `Running on http://0.0.0.0:5000`. Then open a third terminal and run:

```bash
ssh -R 80:localhost:5000 nokey@localhost.run
```

If it asks to continue connecting, type:

```text
yes
```

The tunnel prints a URL like `https://xxxx.lhr.life`. Open that in your browser. If the page is blank, the web UI is not running — go back and check the terminal where you started `causation_web_ui.py`.

Optional smaller vocabulary
---------------------------

![Gold](assets/spectrum/gold.svg) **Gold / constraint:** choose this when the full path is too heavy for the machine.

Run this only if the full vocabulary is too heavy:

```bash
python distill_vocabulary.py --input data/seeded_knowledge_web_250k.json --output data/knowledge_web_distilled.json --target 50000
```

Optional expanded knowledge web
-------------------------------

![Gold](assets/spectrum/gold.svg) **Gold / expansion:** choose this when the machine has room for a larger map.

Run this only if you want a larger knowledge web:

```bash
python reality_simulator/language/expand_knowledge_web.py --input data/seeded_knowledge_web_250k.json --output data/seeded_knowledge_web_expanded.json --concepts 50000 --min-weight 1.5
```

Hardware profiles
-----------------

![Gold](assets/spectrum/gold.svg) **Gold / fit:** match the config to the actual machine, not the wish.

Use `config.json` first. Only use a rented-box profile when the machine actually matches it. For this Space, use `config.json` and update it deliberately.

```bash
python unified_entry.py --config config.json --no-viz --debug
```

Export organisms
----------------

![Violet](assets/spectrum/violet.svg) **Violet / handoff:** package a living result without confusing export with the run itself.

Run one box at a time:

```bash
python cra_cli.py compile-cocoon --top-n 5 --format cocoon
```

```bash
python cra_cli.py compile-cocoon --top-n 5 --format package
```

Do not run this until you replace both alliance IDs. ![Red](assets/spectrum/red.svg) **Red / repair:** placeholders must become real IDs before the shell sees them.

```bash
python cra_cli.py compile-cocoon --alliance-id REPLACE_WITH_ID_1 --alliance-id REPLACE_WITH_ID_2 --format cocoon
```

```bash
python cra_cli.py compile-cocoon --alliance "Alliance Name" --alliance-id REPLACE_WITH_ID_2 --format package
```

```bash
python cra_cli.py cocoon-validate Children/cocoon_ensemble_REPLACE_WITH_TIMESTAMP.zip
```

```bash
python cra_cli.py compile-learning --organism-id REPLACE_WITH_ORGANISM_ID
```

Cocoon plus Champion Council
----------------------------

![Violet](assets/spectrum/violet.svg) **Violet / bridge:** exported beings carry contracts, curriculum, and receipts forward.

Fresh exports include:

- connector-word curriculum in `vocabulary.json`
- bake-time alliance composition with `selected_alliances` and `alliance_ids`
- `game_contracts.json` for Council adapters
- `curriculum/*.json` and `training_logs/schema.json`
- native HTTP endpoints for health, action, learning, chat, teach, vocab, curriculum, training logs, score, snapshot, save, export, and capabilities

Run an exported Cocoon
----------------------

![Green](assets/spectrum/green.svg) **Green / separate life:** run the export as its own body.

Run one box at a time:

```bash
python cocoon.py --mode info --max-organisms 1
```

```bash
python cocoon.py --mode serve --port 8080
```

```bash
python cocoon.py --mode sphere --headless --balls 1 --misses 1 --train
```

```bash
python cocoon.py --mode gym --env CartPole-v1 --episodes 1 --no-learn
```

Persist live learned state
--------------------------

![White](assets/spectrum/white.svg) **White / memory:** save what changed so the run can leave a trace.

Run one box at a time:

```bash
curl -X POST http://localhost:8080/save
```

```bash
curl -X POST http://localhost:8080/export -H "Content-Type: application/json" -d '{"path":"evolved_cocoon.py"}'
```

Tiny rescue card
----------------

![Red](assets/spectrum/red.svg) **Red / repair:** errors are information; read the reason, then take the smallest recovery step.

If setup fails, run:

```bash
python check_setup.py
```

If the world feels empty, run these one at a time:

```bash
python build_curated_dataset.py
```

```bash
python merge_nuclear_vocab.py
```

```bash
python generate_innate_vocab.py
```

If the web view is stale, run:

```bash
python causation_web_ui.py
```

If you get lost, run:

```bash
python cra_cli.py sitrep
```

The whole trick
---------------

![White](assets/spectrum/white.svg) **White / full receipt:** threshold, action, growth, play.

```text
techlady
```

Build the language food. Start the world. Play Pokemon AI, baby.






