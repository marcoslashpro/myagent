# myagent

The name is pretty self explanatory, give a look at the issues to see
what I am planning to do.

**But what can it do now**
For now the agent runs inside of a docker container, and it has the access to
execute bash commands in this python3:12 docker image.

The agent has the possibility to think, code and answer back to the user.

This is currently tested on both `ministral-3:8b` and `qwen3:4b` through `ollama` and they seem to be performing quite nice.
Example scripts are in `examples/` folder.
To run it you'll need to install the examples dependencies with:
```bash
uv sync --examples
```

And then run:
```bash
uv run examples/your_example.py
```

For the official slim version, I intend to be dependency free, I will try to get rid of `rich` when the build is public so that "pretty logging" can be only done
either when installing a cli version or during development.

Speakng of, to run tests:
```bash
uv sync --dev
uv run pytest
```

In the coming future I'll be introducing tool calling and streaming, I also have a very funny idea on how to implement tools for this agent, as well as a context that
can be interacted with programmatically. _Stay tuned..._