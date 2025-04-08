---
title: "Lab 1: Build simple agents with LangGraph"
weight: 1
---

# Build a simple agent using `LangGraph`

## LangGraph

`LangGraph` is an open-source framework designed for building stateful, multi-actor applications with Large Language Models (`LLMs`). It's particularly useful for creating agent and multi-agent workflows with enhanced capabilities beyond simple query-response patterns. In this lab, we will explore how to build a simple travel planner agent using `LangGraph` and how to manage its state effectively using the concept of [`memory`](https://langchain-ai.github.io/langgraph/concepts/memory/) in `LangGraph`.

## Core Definition

`LangGraph` is a specialized orchestration framework that enables developers to create controllable agents with stateful, persistent, and recoverable workflows. It provides infrastructure for building complex LLM applications while maintaining state across interactions.

### Key Components

![lg-diagram](./lg-diagram.png)

1. **State**

    - **State Schema**: Defines the input schema for all nodes and edges in the graph
    - **StateGraph**: A shared data structure that represents the current snapshot of your application
    - **State Management**: Allows tracking variables based on conversation history, task progress, and user preferences

2. **Nodes**

    - **Agent Nodes**: Functions that decide which actions to take
    - **Tool Nodes**: Functions that orchestrate calling tools and returning outputs
    - **Custom Nodes**: User-defined functions that process information

3. **Edges**

    - **Normal Edges**: Direct connections between nodes
    - **Conditional Edges**: Functions that determine which node to call next based on state
    - **Entry Points**: Define which nodes to call first when receiving input

4. **Tools**

    - **Built-in Tools**: Pre-implemented functions like web search tools or database connectors
    - **Custom Tools**: User-created functions that interact with external APIs or data sources

5. **Persistence Layer**

    - **Checkpointers**: Store and retrieve graph state (e.g., `MemorySaver`, `PostgresSaver`)
    - **Memory Management**: Supports both short-term (thread-scoped) and long-term memory. For more information, view [here](https://langchain-ai.github.io/langgraph/concepts/memory/#what-is-memory).

6. **Human-in-the-loop Features**

    - **Interrupt Function**: Allows pausing execution for human input
    - **Tool Review**: Enables humans to review, edit, or approve tool calls

**LangGraph** is part of the **LangChain** ecosystem and is designed to handle complex, multi-step AI workflows that go beyond simple query-response interactions, making it particularly valuable for building sophisticated agent systems.

# Use Case: Build a simple travel planner agent with Memory 

In this lab, we will build a simple travel planner agent using `LangGraph`. The agent will be able to plan a trip based on user input and store the state of the conversation for future reference. We will use the `LangGraph` library to create a stateful agent that can remember user preferences and past interactions. 

## Steps to run

Follow the prerequisites from before to clone the GitHub repository and install `uv` and the required packages. 

**Open Lab 1: Build a simple agent using `LangGraph`** ([build_simple_single_agent_langgraph.ipynb](https://github.com/madhurprash/langGraph-AWS-incident-response/blob/main/scratchpad_examples/build_simple_single_agent_langgraph.ipynb)) and run each cell step by step.

#### Step 1: We first define the agent state

As a first step, we will define the agent state that remains throughout the course of the agent execution workflow. This includes the state of the graph that contains a state schema. This schema servers as the input for all nodes and edges in the graph.

```python
# We create a class `PlannerState` that defines the state of the agent.
class PlannerState(TypedDict):
    # holds the list of conversation messages between AI and the User. Maintaining this conversation history
    # allows the agent to refer to the previous interactions and provide contextually relevant responses.
    messages: Annotated[List[HumanMessage | AIMessage], "The messages in the conversation"]
    # This is a string that stores the current state of the trip itinerary.
    itinerary: str
    # This is a field that records the user's preferences for a city for the trip. This can be used by the agent
    # to provide personalized recommendations.
    city: str
    # This is the most recent message from the user.
    user_message: str
```

By managing these elements within the `PlannerState`, the agent can effectively use the conversation's context and state and hence, this facilitates a more dynamic and coherent interaction.

#### Step 2: Set up the Large Language Model (LLM)

In this step, we will set up the Large Language Model (LLM) that will be used by the agent to generate responses. We will use the `Amazon Bedrock`'s `Amazon Nova` models using the [`ChatBedrockConverse`](https://api.python.langchain.com/en/latest/aws/chat_models/langchain_aws.chat_models.bedrock_converse.ChatBedrockConverse.html) on `LangGraph`. This is the bedrock chat model integration build on the Bedrock converse API. 

```python
# Create the llm used by the agent
llm = ChatBedrockConverse(
    # this is a chat model class that enables you to use the Bedrock API
    model=AMAZON_NOVA_LITE_MODEL_ID,
    # Provider is 'bedrock'
    provider=PROVIDER_ID, 
    # inference parameters - temperature controls the randomness of the model's output
    # lower temperature values make the output more deterministic, while higher values make it more random
    temperature=TEMPERATURE, 
    max_tokens=MAX_TOKENS,
    client=bedrock_client,
)

# Initialize the itinerary prompt that will be used across the agent workflow. This gives agent instructions and guidance while executing tasks based on the user request. The ChatPromptTemplate gives a prompt template for chat models
ITINERARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful travel assistant. Create a day trip itinerary for {city} based on the user's interests. 
    Follow these instructions:
    1. Use the below chat conversation and the latest input from Human to get the user interests.
    2. Always account for travel time and meal times - if its not possible to do everything, then say so.
    3. If the user hasn't stated a time of year or season, assume summer season in {city} and state this assumption in your response.
    4. If the user hasn't stated a travel budget, assume a reasonable dollar amount and state this assumption in your response.
    5. Provide a brief, bulleted itinerary in chronological order with specific hours of day."""),
    # Users can provide a message history that will be replaced in the prompt to provide a revised itinerary
    MessagesPlaceholder("chat_history"),
    ("human", "{user_message}"),
])
```

#### Step 3: Define the agent nodes and edges

In `langGraph`, nodes and edges are fundamental concepts that define the structure of the computational graph. `Nodes` represent the units of computation that contain some logic to perform specific tasks within the workflow. It takes the current input, executes the function and produces an output that updates the graph's state. On the other hand, `edges` represent the connections between nodes, defining the flow of data and control within the graph. They determine how the output of one node is passed as input to another node.

```python
# The first node that we will create will solely input a user message
def input_interest(state: PlannerState) -> PlannerState:
    .
    .
    .
    .
    }

# The next node is responsible for creating an agent invocation based on the user interest
def create_itinerary(state: PlannerState) -> PlannerState:
    .
    .
    .
    .
    }
```

1. We will use the `input_interest` as the first node that will capture the user's travel interests - including the user input and the city of interest and will update the `PlannerState` with the user message.

2. The `create_itinerary` node is responsible for creating an agent invocation based on the user interest. This node will use the `ITINERARY_PROMPT` to generate a travel itinerary based on the user's preferences and the city of interest.

#### Step 4: Create and compile the graph

Next, once we have established and executed the `landGraph` workflow, we will:

3. **Initialize the StateGraph**: Here, we will create a `StateGraph` object called `workflow`. This class is responsible for managing the state of the graph and its nodes. We will also set up the initial state of the graph using the `PlannerState` class we defined earlier.

    ```python
    workflow = StateGraph(PlannerState)
    ```

4. **Add Nodes to the workflow**: Next, we add two primary nodes to the workflow. One is the `input_user_interests` node that captures the user request and the city of interest. The second node is `create_itinerary` that generates the travel itinerary based on the user input and the city of interest.

    ```python
    workflow.add_node("input_user_interests", input_interest)
    workflow.add_node("create_itinerary", create_itinerary)
    ```

5. **Set entry point**: Next, we define the entry point of the graph as the `input_user_interests` node. This means that when the graph is executed, it will start from this node.

    ```python
    workflow.set_entry_point("input_user_interests")
    ```

6. **Define edges between nodes**: Edges are established to dictate the flow between the nodes. These nodes can either be direct from one node to another or conditional.

    ```python
    workflow.add_edge("input_user_interests", "create_itinerary")
    workflow.add_edge("create_itinerary", END)
    ```

7. **Implement persistent memory**: A `MemorySaver` is employed to persist the state of the graph across sessions, allowing for continuity in user interactions. `LangGraph` has a built-in persistence layer implemented through `checkpointers`.

    ```python
    memory = MemorySaver()
    ```

8. **Compile the graph**: The `workflow` is compiled into an executable application, incorporating the defined nodes, edges, and persistent memory. When you compile the graph with a `checkpointer`, the `checkpoint` are saved to a `thread`. This can be accessed after the graph execution. Because `threads` allow access to graph's state after execution, several powerful capabilities including **human-in-the-loop, memory, time travel, and fault-tolerance** are all possible.

    ```python
    app - workflow.compile(checkpoint=memory)
    ```

9. **Execute the graph using persistent memory**: The workflow is executed with specific user inputs and a configuration dictionary that includes a `thread_id`. This `thread_id` serves as a unique identifier for the conversation session, enabling the graph to maintain separate conversation histories for different sessions.

    ```python
    config = {"configurable": {"thread_id": "1"}}

    user_request = input("Enter your travel request: ")
    city = input("Enter the city: ")

    run_travel_planner(user_request, city, config)
    ```

As we maintain the same `thread_id`, we can keep asking and engaging with the agent and seeing the same trip itinerary update based on user requests. Once another `thread_id` is used, the agent will not remember the previous conversation and will start a new conversation with the user.

## Memory    

Memory is key for any `agentic` conversation which is Multi-Turn or Multi-Agent collaboration conversation and more so if it spans multiple days. The 3 main aspects of Agents are:

1. Tools
1. Memory
1. Planners

In `LangGraph`, we can use the `Memory` class to persist the state of the graph across sessions. Two primary patterns can be employed:​

- **Agent-Specific Session Memory**: Each agent maintains its own isolated session memory, allowing for individualized context management.​ This can also be referred to as **short term memory**, or thread scoped memory. Once the graph is compiled with a `checkpointer`, you can save the agent session memory using a `thread_id` in a configuration. This `thread_id` will store the state of that graph execution enabling users to add in human in the loop, fault tolerance and also other relevant steps here.

- **Graph-Level Combined Memory**: A unified memory shared across the entire graph, enabling all agents to access and contribute to a common context. We can think of this as when there are several users using the application and context needs to be stored across users. In this case, we can use **long term memory** which is shared across conversational threads. It can be recalled at any time.

### Agent-Specific Session Memory

In this pattern, we can add thread scoped memory to the agent. This thread will contain the conversation history and the state of the agent. This is useful when we want to maintain the context of the conversation for a specific conversation. In the example below, we will see how the itinerary planner will create the itinerary based on the user input and the city of interest. The agent will remember the conversation history and the state of the agent. When we ask a new question with the same thread id, the agent will remember the previous conversation and will create a new itinerary based on the user input and the city of interest.

```python
config = {"configurable": {"thread_id": "1"}}

# I want to create an itinerary for a day trip in seattle with boaring and swimming options. Make it extremely comprehensive and should include meals as well
user_request = input("Enter your travel request: ")
# Seattle
city = input("Enter the city: ")

# Use them in the function call
run_travel_planner(user_request, city, config)
```

Next, we will ask the agent with the same `thread_id` to add "picnic" to the itinerary. The agent will remember the previous conversation and will create a new itinerary based on the user input and the city of interest.

### Custom Memory Store Implementation

In this example the `CustomMeoryStore` class is created that wraps around a base storage system at the user level. In this case, the implementation shows how to store the user with a `namespace` and the item or messages from that users in the `memory` store. The `CustomMemoryStore` class implements the `MemoryStore` interface and provides methods to add, get, and delete items from the memory store. The `CustomMemoryStore` class is used in the agent to persist the state of the graph across sessions, allowing for continuity in user interactions.

```python
from langgraph.store.base import BaseStore, Item, Op, Result
from langgraph.store.memory import InMemoryStore
from typing import Any, Iterable, Literal, NamedTuple, Optional, Union, cast

# CustomMemoryStore is a wrapper class that implements the BaseStore interface
class CustomMemoryStore(BaseStore):
    def __init__(self, ext_store):
        # Initialize with an external store that will handle the actual storage
        self.store = ext_store

    def get(self, namespace: tuple[str, ...], key: str) -> Optional[Item]:
        # Retrieve an item from the store using namespace and key
        return self.store.get(namespace, key)

    def put(self, namespace: tuple[str, ...], key: str, value: dict[str, Any]) -> None:
        # Store a value in the store using namespace and key
        return self.store.put(namespace, key, value)
        
    def batch(self, ops: Iterable[Op]) -> list[Result]:
        # Execute multiple operations in a batch
        return self.store.batch(ops)
        
    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        # Execute multiple operations asynchronously in a batch
        return self.store.abatch(ops)
```

In this case, when we initialize the `create_itinerary` node, we will use the `CustomMemoryStore` class to persist the state of the graph across sessions using the user's namespace and first get the messages from the `CustomMemoryStore` class. In this case, we will not be using the `messages` variable in the `PlannerState` class because the messages will be stored at the user level in the `CustomMemoryStore` class. 

```python
def create_itinerary(state: PlannerState, config: RunnableConfig, *, store: BaseStore) -> PlannerState:
    #- get the history from the store
    user_u = f"user_id_{config['configurable']['thread_id']}"
    namespace_u = ("chat_messages", user_u)
    store_item = store.get(namespace=namespace_u, key=user_u)
    chat_history_messages = store_item.value['data'] if store_item else []
    print(user_u,chat_history_messages)

    response = llm.invoke(ITINERARY_PROMPT.format_messages(city=state['city'], user_message=state['user_message'], chat_history=chat_history_messages))
    print("\nFinal Itinerary:")
    print(response.content)

    #- add back to the store
    store.put(namespace=namespace_u, key=user_u, value={"data":chat_history_messages+[HumanMessage(content=state['user_message']),AIMessage(content=response.content)]})
    
    return {
        **state,
        "itinerary": response.content
    }
```

### Retrieve memory from the store

You can also retrieve the chat messages for a given user from the in memory store. This is useful when you want to get the chat history for a specific user and use it in the agent workflow. In this case, we will use the `get` method of the `CustomMemoryStore` class to retrieve the chat messages for a given user.

```python
print(in_memory_store_n.get(('chat_messages', 'user_id_1'),'user_id_1').value)
```

Output:

```python
[('chat_messages', 'user_id_1')]
{'data': [HumanMessage(content='Can you create a itinerary for a day trip in london... AIMessage(content="Day Trip Itinerary for London**\n\n**Assumptions:**\n- Season: Summer\n- Budget: $150\n\n**Itinerary:**\n\n- **8:00 AM - 9:00 AM: Breakfast at...
```

**Some more bonus information on Long-term memory on `LangGraph`**: `LangGraph` stores long-term memories as JSON documents in a store (reference doc). Each memory is organized under a custom namespace (similar to a folder) and a distinct key (like a filename). Namespaces often include user or org IDs or other labels that makes it easier to organize information. For more information, view: https://langchain-ai.github.io/langgraph/concepts/memory/#storing-memories.

