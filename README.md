# g1: Early Prototype of Using Llama-3.1 70b on Groq to create o1-like reasoning chains

This is an early prototype of using prompting strategies to improve the LLM's reasoning capabilities through o1-like reasoning chains. This allows the LLM to "think" and solve logical problems that usually otherwise stump leading models. Unlike o1, all the reasoning tokens are shown.

### Examples

> [!IMPORTANT]
> g1 is not perfect, but seems to perform significantly better than LLMs out-of-the-box. From initial testing, g1 accurately solves logic problems 60-80% of the time that usually stump LLMs. See examples below.


##### How many Rs are in strawberry?
Prompt: How many Rs are in strawberry?

Result:
[Strawberry example](examples/strawberry.png)


### Prompting Strategy