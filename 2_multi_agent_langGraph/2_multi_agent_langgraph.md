---
title: "Lab 3: Multi-agent system LangGraph"
weight: 3
---

# Build a multi-agent system using `LangGraph`

## Challenges with single agents

Single agent systems are not efficient for diverse tasks or for applications which may require multiple tools. Imagine input context size if have to use 100s of tools. Each tool has its own description and input/output schema. In such cases, it is difficult to use a single model that can handle all the tools.

Some of the common challenges are:

1. Lack of flexibility: our agentic application is limited to one LLM
1. Contextual overload - too much information in the context
1. Lack of parallel processing
1. Single point of failure

### Why multi agents?

While building single agents systems using `LangGraph` is simple, as your use case grows and scales, it is important to understand what would be needed for your solution to truly scale. If you have several domain specific agents assigned to different tasks, creating and managing each of these agents separately becomes an overhead. To split and scale these organizational level tasks and manage the orchestration, you can use multi agents. Multi agents enables agent developers to delegate tasks to sub agents through a supervisor agent and enable agent to agent communication. These agents can have access to specific tools per sub task.

### The primary benefits of using multi-agent systems are:

1. **Modularity**: Separate agents make it easier to develop, test, and maintain `agentic` systems.

2. **Specialization**: You can create expert agents focused on specific domains, which helps with the overall system performance.

3. **Control**: You can explicitly control how agents communicate (as opposed to relying on function calling).

#### What gets covered in this lab:

1. Multi Agent collaboration
1. Leverage memory for 'turn-by-turn' conversations
1. Leverage Tools like API's and RAG for searching for answers.
1. Use Human In the loop for some critical workflows

## Multi-agent architectures

1. **Network Architecture**: In this model, each agent can communicate with every other agent in a many-to-many relationship. Any agent can decide which other agent to call next. This works well for problems without a clear hierarchy or specific calling sequence.

2. **Supervisor Architecture**: Here, each agent communicates with a single supervisor agent that makes decisions about which agent should be called next. This centralizes decision-making.

3. **Supervisor (tool-calling)**: This is a special case of the supervisor architecture where individual agents are represented as tools. The supervisor agent uses a tool-calling LLM to decide which agent tools to call and what arguments to pass to them.

4. **Hierarchical Architecture**: This extends the supervisor concept by creating a "supervisor of supervisors." It generalizes the supervisor architecture to allow for more complex control flows, essentially creating teams of agents with their own supervisors, all managed by a top-level supervisor.

5. **Custom Multi-agent Workflow**: In this architecture, each agent communicates with only a subset of other agents. Some parts of the flow are deterministic (predetermined), while only certain agents have the ability to decide which other agents to call next.

![mac-patterns](/amazon-bedrock-modular-overview/static/080-agents-with-langgraph/083-multi-agent/mac-patterns.png)

## Main Components of the Multi-Agent System

![mac-diagram](/amazon-bedrock-modular-overview/static/080-agents-with-langgraph/083-multi-agent/mac.png)

1. **Supervisor Agent**

- Acts as a central coordinator for the multi-agent system
- Routes user requests to appropriate specialized agents
- Maintains conversation flow between agents
- Makes decisions about task completion
- Uses a structured output chain to determine the next agent to call

2. **Flight Agent**

- Specialized agent handling flight-related queries
- Implements the ReAct pattern (reasoning and acting)

- Tools:
    1. Search flights
    1. Retrieve flight booking information
    1. Change flight booking dates
    1. Cancel flight bookings

3. **Hotel Agent**

- Specialized agent handling hotel-related queries
- Implements a custom architecture with human-in-the-loop capability

- Tools:
    1. Suggest hotels
    1. Retrieve hotel booking information
    1. Change hotel booking dates
    1. Cancel hotel bookings

4. Human-in-the-Loop

- `HumanApprovalToolNode` for critical operations
- Interrupts execution for user confirmation
- Processes user input to approve or deny actions

## Steps to run

Follow the prerequisites from before to clone the GitHub repository and install `uv` and the required packages. 

1. Open **Lab 3: Build a multi-agent using `LangGraph` with `tools` and Human-in-the-loop (`HITL`)** ([advance-langgraph-multi-agent-setup.ipynb](https://github.com/madhurprash/langGraph-AWS-incident-response/blob/main/scratchpad_examples/advance-langgraph-multi-agent-setup.ipynb)) and run each notebook step by step.



