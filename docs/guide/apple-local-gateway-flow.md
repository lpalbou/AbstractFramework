# Apple Silicon local Gateway + Flow quickstart

This is the shortest path for a new Apple Silicon user who wants AbstractGateway and AbstractFlow running locally with a local MLX model. No OpenAI, Anthropic, or hosted provider key is required.

## Requirements

- Apple Silicon Mac: M1, M2, M3, M4, or newer.
- Python 3.10 to 3.12.
- Node.js 20 or newer for the Flow web editor.
- Enough disk space for the Python stack and a local MLX model.

## Install

1. Create a clean Python environment.

```bash
python3 -m venv .venv-abstract
source .venv-abstract/bin/activate
python -m pip install -U pip wheel setuptools
```

2. Install the local Apple Gateway profile.

```bash
pip install "abstractgateway[apple]"
```

3. Download a small MLX model into the Hugging Face cache.

```bash
huggingface-cli download mlx-community/Qwen3-4B-4bit
```

## Start Gateway

Run this in terminal 1.

```bash
source .venv-abstract/bin/activate

export ABSTRACTGATEWAY_DATA_DIR="$HOME/.abstractgateway-local"
export ABSTRACTGATEWAY_USER_AUTH=1

abstractgateway-config set-default input.text \
  --provider mlx \
  --model mlx-community/Qwen3-4B-4bit

abstractgateway serve --host 127.0.0.1 --port 8080
```

The Gateway API is now at `http://127.0.0.1:8080`.

Gateway creates `default/admin` if needed and writes the browser-login token to
`$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token`:

```bash
cat "$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token"
```

Use that token with Gateway user `admin`.

## Start Flow

Run this in terminal 2.

```bash
npx @abstractframework/flow \
  --gateway-url http://127.0.0.1:8080 \
  --port 3003
```

Open `http://127.0.0.1:3003` and sign in as user `admin` with the generated
Gateway user token.

## Create and run a first workflow

1. Create a new flow in the editor.
2. Add `On Flow Start`.
3. Add `LLM Call`.
4. Connect `On Flow Start` to `LLM Call`.
5. Set the LLM prompt to `Say hello in one short sentence.`.
6. Leave provider/model unset to use the Gateway defaults, or explicitly select `mlx` and `mlx-community/Qwen3-4B-4bit`.
7. Add an output/end node if the editor template requires one.
8. Save.
9. Publish.
10. Run.

## Smoke checks

Run these while Gateway is still running.

```bash
curl -s \
  -H "Authorization: Bearer $(cat "$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token")" \
  http://127.0.0.1:8080/api/gateway/discovery/capabilities | python -m json.tool

curl -s \
  -H "Authorization: Bearer $(cat "$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token")" \
  http://127.0.0.1:8080/api/gateway/discovery/providers | python -m json.tool
```

Expected result:

- `capabilities.abstractgateway.installed` is `true`.
- `capabilities.contracts.common.runs.input_data` is present, or the Flow UI can still fall back to `/api/gateway/runs/{run_id}/input_data`.
- `default_provider` is `mlx`.
- `default_model` is `mlx-community/Qwen3-4B-4bit`.

## If Flow says input rehydration is missing

That warning means Flow did not see the run input-data contract in Gateway discovery. The usual causes are a stale Gateway process, an older installed `abstractgateway`, or a Flow proxy pointed at the wrong Gateway URL.

Fix:

```bash
pip install -U "abstractgateway[apple]"
abstractgateway serve --host 127.0.0.1 --port 8080
```

Then restart the Flow process with the same `--gateway-url` and sign in again if
the browser session is no longer present.

## Optional local Ollama alternative

If you prefer Ollama instead of in-process MLX, install Ollama, pull a model, and change only the
`input.text` route.

```bash
ollama pull qwen3:4b-instruct

abstractgateway-config set-default input.text \
  --provider ollama \
  --model qwen3:4b-instruct
abstractgateway serve --host 127.0.0.1 --port 8080
```
