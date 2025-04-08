---
title: "Lab 2: Adding Tools to LangGraph Agents"
weight: 2
---

# Adding Tools to `LangGraph` Agents

`Tools` are an abstraction in `LangChain` that associates a python function with a schema that defines the function's name, description and expected arguments. `Tools` can then be passed to chat models that support tool calling allowing the model to request the execution of that function with the required parameters as provided in the schema.

This lab provides guidance on implementing and using tools with `LangGraph` agents. `LangGraph` is an open-source framework for building stateful, multi-actor applications with Large Language Models (`LLMs`). Tools extend the capabilities of these agents by allowing them to interact with external systems and APIs. We will use the same example from lab 1, where we built a simple agent that can answer questions about planning trip itineraries. In this lab, we will add tools that allow the agent to access the some APIs that it can use to answer the questions with more real life live data.

## What is Tool Calling?

Many AI applications interact directly with humans but what if there was a way for Large Language Models (LLMs) to interact directly with systems, such as your databases or external APIs? These systems often have a specific input schema, for example APIs frequently require a payload structure. For this, tool calling enables this functionality:

1. **Tool Creation**: Use the @tool decorator to create a tool. A tool is an association between a function and its respective schema.

1. **Tool Binding**: The tool needs to be connected to a model that supports tool calling. This gives model the awareness of the tool and the associated input schema that is required.

1. **Tool Calling**: When appropriate, the model can decide to call a tool and ensure its response conforms to the tool's output schema.

1. **Tool Execution**: The tool can be executed using the arguments provided by the model.

## Steps to run

Follow the prerequisites from before to clone the GitHub repository and install `uv` and the required packages. 

1. Open **Lab 2: Build a simple agent using `LangGraph` with `tools`** ([add_tools_to_simple_agent.ipynb](https://github.com/madhurprash/langGraph-AWS-incident-response/blob/main/scratchpad_examples/add_tools_to_simple_agent.ipynb)): 

### Step 1: State Definition

The `PlannerState` class defines what data the agent will track throughout its execution cycle. This includes:

- `messages`: A history of the conversation between the human and AI
- `itinerary`: The final travel plan created by the agent
- `city`: The destination city for the trip
- `user_message`: The latest message from the user
- `weather_info` and `attractions_info`: Optional fields to store information retrieved by the tools
This state schema serves as a central repository that all nodes in the graph can access and modify.

### Step 2: Tool Creation

The code defines two tools using the `@tool` decorator:

1. `mock_search_tourist_attractions`: Retrieves tourist attractions for a given city
1. `mock_get_weather_forecast`: Retrieves weather information for a given city

We will use the following `bind_with_tools` function to bind the tools to the agent:

```python
# Tool creation
tools = [my_tool]
# Tool binding
model_with_tools = model.bind_tools(tools)
# Tool calling 
response = model_with_tools.invoke(user_input)
```

View the tool creations and providing it to the `ReAct` agent in the code below:

```python
from langchain_core.tools import tool
import json
import os

@tool
def mock_search_tourist_attractions(city: str) -> str:
    return pass

@tool
def mock_get_weather_forecast(city: str) -> str:
    return pass

# Define the tool list
tools = [mock_search_tourist_attractions, mock_get_weather_forecast]

from langgraph.prebuilt import create_react_agent

# Create the ReAct agent with the correct prompt
get_realtime_info_react_llm = create_react_agent(
    llm,
    tools=tools
)
```

In this code, we define two tools: `mock_search_tourist_attractions` and `mock_get_weather_forecast`. Each tool is a function that takes a city name as input and returns a string. The `@tool` decorator registers these functions as tools in the `LangGraph` framework.

Both the tools are designed to return a string that fetches some data from the locally residing and synthetically created data within the `attractions.json` and `weather.json` files. The `mock_search_tourist_attractions` function retrieves tourist attractions for a given city, while the `mock_get_weather_forecast` function retrieves weather information for that city. In an ideal scenario, these functions would call an external API to fetch real-time data.

### Step 3: Tool Binding

The tools are bundled into a list and passed to the `create_react_agent` function along with the LLM (in this case, Amazon Bedrock's Nova Lite model). This creates a `ReAct` (Reasoning and Acting) agent that can:

- Reason about what tool to use based on the user's query
- Call the appropriate tool with the correct parameters
- Process the tool's response and incorporate it into its final answer

View an example of a user invocation and the agent's response:

```python
config = {"configurable": {"thread_id": "thread_1"}}
input_data = {"user_message": "I'm interested in visiting Paris for 3 days and I love art, history, and food. Can you suggest an itinerary?"}

# Run the workflow with your input
result = app.invoke(input_data, config=config)
```

Output:

```json
{
  "messages": [
    {
      "type": "HumanMessage",
      "content": "I'm interested in visiting London for 3 days. Can you suggest an itinerary?",
      "id": "2153ddbe-4104-4854-ab93-5098b348cec8"
    },
    {
      "type": "AIMessage",
      "content": [
        {
          "type": "text",
          "text": "<thinking>The User wants to visit London for 3 days and needs an itinerary. I can suggest some tourist attractions in London using the mock_search_tourist_attractions tool. I can also suggest a rough itinerary based on the attractions.</thinking>\n"
        },
        {
          "type": "tool_use",
          "name": "mock_search_tourist_attractions",
          "input": {
            "city": "London"
          },
          "id": "tooluse_HE6FsZ80T8mNJIE78h_u0w"
        }
      ],
      "id": "run-e1c23e22-01cc-4583-81b7-a1dfbbec91e3-0",
      "tool_calls": [
        {
          "name": "mock_search_tourist_attractions",
          "args": {
            "city": "London"
          },
          "id": "tooluse_HE6FsZ80T8mNJIE78h_u0w",
          "type": "tool_call"
        }
      ],
      "usage_metadata": {
        "input_tokens": 528,
        "output_tokens": 94,
        "total_tokens": 622
      }
    },
    {
      "type": "ToolMessage",
      "content": "Top boating and swimming attractions in London:\n1. River Thames Boat Tours: Experience London from a unique perspective with a relaxing boat tour along the River Thames. These tours offer spectacular views of iconic landmarks ...\n2. Hyde Park Serpentine Lido: A popular swimming spot in the heart of London, the Serpentine Lido offers a refreshing escape from the city heat during summer months. The facility i...\n3. Hampstead Heath Swimming Ponds: These natural swimming ponds are a beloved tradition in London. With separate ponds for men, women, and mixed groups, they offer a unique wild swimmin...\n",
      "name": "mock_search_tourist_attractions",
      "id": "04233309-f8d1-4bd7-8b75-f7b950c07fd7",
      "tool_call_id": "tooluse_HE6FsZ80T8mNJIE78h_u0w"
    },
    {
      "type": "AIMessage",
      "content": "<thinking>I have retrieved the information about tourist attractions in London. Based on the attractions, I can suggest a rough itinerary for the User's 3-day visit.</thinking>\n\nHere's a suggested itinerary for your 3-day visit to London:\n\n**Day 1: Historical and Cultural Exploration**\n- Morning: Start your day with a boat tour along the River Thames. This will give you a unique perspective of London and its iconic landmarks.\n- Afternoon: Visit the British Museum, which houses a vast collection of world art and artifacts.\n- Evening: Explore the historic district of Covent Garden, known for its vibrant street performances and boutique shops.\n\n**Day 2: Nature and Outdoor Activities**\n- Morning: Head to Hyde Park and enjoy a swim at the Serpentine Lido, a popular swimming spot in the heart of London.\n- Afternoon: Visit Kensington Gardens and the Royal Botanic Gardens, Kew, which offer beautiful outdoor spaces to relax and explore.\n- Evening: Take a leisurely walk along the River Thames and enjoy the evening views of the city.\n\n**Day 3: Local Experiences and Shopping**\n- Morning: Visit Hampstead Heath and swim in one of the natural swimming ponds, a beloved tradition in London.\n- Afternoon: Explore the local markets, such as Portobello Road Market, for unique souvenirs and local products.\n- Evening: Enjoy a West End show or dinner at a local restaurant to end your trip on a high note.\n\nPlease note that this is a rough itinerary and you can adjust it based on your interests and preferences. Enjoy your trip to London!",
      "id": "run-15afc9e3-dd6b-4f07-a147-2884980a7e81-0",
      "usage_metadata": {
        "input_tokens": 749,
        "output_tokens": 318,
        "total_tokens": 1067
      }
    }
  ]
}
```

### More about Tools in `LangGraph`
---

From the example above and other discussions, there are various ways to create tools using `LangGraph`:

1. Creating Tools with the `@tool` Decorator:

  ```python
  from langchain_core.tools import tool

  @tool
  def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
  ```

This decorator simplifies tool creation by automatically inferring the tool's name, description, and expected arguments from the function definition.

2. Using Tools Directly:

  ```python
  multiply.invoke({"a": 2, "b": 3})

  # You can also inspect a tool's properties:
  print(multiply.name)  # multiply
  print(multiply.description)  # Multiply two numbers.
  print(multiply.args)  # JSON schema of the arguments
  ```

3. **Configuring Tool Schema**: You can customize a tool's schema by providing additional parameters to the @tool decorator, such as modifying the name, description, or parsing the function's docstring.

4. Working with Tool Artifacts:

Tools can return artifacts that should be accessible to downstream components but not directly exposed to the model:

  ```python
  @tool(response_format="content_and_artifact")
  def some_tool(...) -> Tuple[str, Any]:
      """Tool that does something."""
      ...
      return 'Message for chat model', some_artifact
  ```

5. Using Special Type Annotations: 

Several special type annotations can be used in tool function signatures:

  - **InjectedToolArg**: For arguments that shouldn't be exposed to the model
  - **RunnableConfig**: To access the `RunnableConfig` object
  - **InjectedState**: To access the overall state of the `LangGraph` graph
  - **InjectedStore**: To access the `LangGraph` store object

  ```python
  from langchain_core.tools import tool, InjectedToolArg
  @tool
  def user_specific_tool(input_data: str, user_id: InjectedToolArg) -> str:
      """Tool that processes input data."""
      return f"User {user_id} processed {input_data}"
  ```

6. Using Annotated Types for Descriptions: 

  ```python
  from typing import Annotated

  @tool
  def search_tool(query: Annotated[str, "The search query to execute"]) -> str:
      """Search for information."""
      return f"Results for {query}"
  ```

7. **Using Toolkits**

`LangGraph` has a concept of `toolkits` that group related tools together:

  ```python
  # Initialize a toolkit
  toolkit = ExampleToolkit(...)

  # Get list of tools
  tools = toolkit.get_tools()
  ```

