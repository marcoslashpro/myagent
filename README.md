# myagent

The name is pretty self explanatory, give a look at the issues to see
what I am planning to do.

**But what can it do now**
For now the agent runs inside of a docker container, and it has the access to
execute bash commands in this python3:12 docker image.

The agent has the possibility to think, code and answer back to the user.

This is currently tested on both `ministral-3:8b` and `qwen3:4b` through `ollama`, an example script is in `tests/ollama_agent.py` and it should probably be moved to a `examples/` folder. To run it you'll need to install the dev dependencies with:

```
uv sync
```

For the rest, I aim to be dependency free, except for the docker client.

In the coming future I'll be introducing tool calling and streaming, I also have a very funny idea on how to implement tools for this agent, as well as a context that
can be interacted with programmatically. _Stay tuned..._