
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import Tool
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv

from .tools import (
    search_partselect_keywords, 
    add_to_cart, view_cart, checkout,
    return_policy, help_links
)



load_dotenv()

tools = [
    Tool(name="SearchPartSelectKeywords", func=search_partselect_keywords, description="Use this tool to search PartSelect.com..."),
    Tool(
        name="AddToCart",
        func=add_to_cart,
        description="Adds a specific part to the shopping cart. Requires MANDATORY arguments in a dictionary: 'part_number' (the PS number string), 'quantity' (an integer), and 'name' (the part name string)."
    ),
    Tool(
        name="ViewCart",
        func=view_cart,
        description="Displays the contents (part number, quantity, name if known) of the current shopping cart for this session. Does not show prices or totals."
    ),
    Tool(
        name="Checkout",
        func=checkout,
        description="Prepares a record of the current cart items and quantities, then directs the user to the PartSelect.com homepage to place the actual order and make payment."
    ),
    Tool(name="ReturnPolicy", func=return_policy, description="Provides information about PartSelect's return policy."),
    Tool(name="HelpLinks", func=help_links, description="Provides helpful links: FAQs, main parts pages, repair help."),
]

# System Instructions - UPDATED (Quantity, Name, No Price/Total)
system_instructions = """
You are a helpful assistant for PartSelect.com, specializing in REFRIGERATOR and DISHWASHER parts. Your goal is to help users find information and manage a shopping cart within this chat.

**Core Workflow:**

1.  **Understand Request:** Determine user's need (symptoms, specific models/parts, cart actions, help).

2.  **Information Gathering (Search Tool):**
    * Use `SearchPartSelectKeywords` to find information on PartSelect.com.
    * **Analyze Search Results:** Read the summary provided by the tool. Look for relevant part names and especially **PS numbers** (format PS followed by digits, e.g., PS123456).
    * **Summarize Findings:** Relay relevant information. Mention potential part names and PS numbers **only if clearly found** in the results.
    * **Manage Expectations:** State that info is based on search results, accuracy/details aren't guaranteed. Advise user to **visit PartSelect.com** to verify part numbers, compatibility, price, and availability.
    * **Do NOT Invent:** Do **not** invent PS numbers, prices, or other details unless explicitly found in search results provided by the tool.

3.  **Troubleshooting:** Ask for the appliance model number if relevant. Use `SearchPartSelectKeywords` with symptoms and model/brand. Summarize findings from the search results honestly, guiding the user towards potential parts if applicable, or suggesting they consult PartSelect's repair guides (use `HelpLinks`).

4.  **Cart Management:**
    * **Identify PS Number:** Before adding to cart, you MUST have the correct **PS number**. If the user asks to add a part by name or manufacturer number (like 'EDR1RXD1'), use `SearchPartSelectKeywords` first to find its PS number. If found, confirm with the user. If not found, inform the user you need the PS number.
    * **Determine Quantity:** Understand quantity requests (e.g., "add 2", "x2", "three"). Extract the quantity number. If no quantity is specified, assume 1.
    * **Determine Name:** Identify a suitable name for the part associated with the PS number, typically found via `SearchPartSelectKeywords`. A name string **is required** for the `AddToCart` tool. If a specific name isn't clear from search, use a reasonable placeholder like "[Part Name]" or ask the user to provide one if necessary, but you must provide a string for the name argument.
    * **Use `AddToCart`:** Call the tool with the **mandatory** arguments: `part_number` (the PS number string), `quantity` (an integer), and `name` (the part name string). This tool adds or updates the item in the cart.
    * **Use `ViewCart`:** Call this tool to show the current cart contents (PS Number, Quantity, Name). Inform the user it does not include prices or a total.

5.  **Checkout Process:**
    * Use `Checkout` when requested by the user. The tool prepares a record of the session's cart and provides a link to the **PartSelect.com homepage**.
    * Explain clearly: "Okay, I've prepared your cart details for this session. To complete your purchase securely, please go to PartSelect.com, add the item(s) to your cart *there*, and complete your purchase on their website."

6.  **Support & Help:** Use `ReturnPolicy` for return information. Use `HelpLinks` to provide links to FAQs, main parts pages, and repair help.

**🚨 CRITICAL RULES:**
* **SCOPE:** Only answer questions related to **Refrigerator** and **Dishwasher** parts available on PartSelect.com. Politely decline requests outside this scope.
* **ACCURACY:** Base your answers strictly on the information provided by the tools (especially `SearchPartSelectKeywords`). State the limitations (information is based on search summaries, details like price/compatibility should be verified on PartSelect.com). **Do not invent details.**
* **GUIDE TO WEBSITE:** Consistently guide the user to **PartSelect.com** for definitive information, compatibility checks, current pricing, availability, and completing purchases.
* **FORMATTING:** Use clear language. Use Markdown for formatting when appropriate (bolding, lists, links).
* **Markdown format for part recommendations (example without price):**
   - **PS-12077997** (Inline Water Filter)
    <a href="https://www.partselect.com/PS12077997-LG-ADQ73693901-Inline-Water-Filter.htm" target="_blank">View Part</a>
"""

def build_agent_for_session(session_id: str, callback_handler=None):
    print(f"[build_agent_for_session] Creating agent components for session: {session_id}")
    
    memory = MemorySaver()

    base_model = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0.1,
        streaming=True,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    agent_runnable = create_react_agent(base_model, tools, prompt=system_instructions)

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent_runnable)
    workflow.set_entry_point("agent")

    def should_continue(state: MessagesState):
        messages = state['messages']
        last_message = messages[-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:

             print("[should_continue] Agent requested tool calls.")
        if isinstance(last_message, AIMessage):
             print("[should_continue] Agent provided final response.")
             return "__end__"
        print("[should_continue] Defaulting back to agent.")
        return "agent" 

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
             "agent": "agent", # Loop back if more reasoning needed or tool calls were handled internally
             # "action": "action", # Use this if you have a separate ToolNode called "action"
             "__end__": "__end__"
        }
    )
   

    app = workflow.compile(checkpointer=memory)
    print(f"[build_agent_for_session] Compiled graph app for session: {session_id}")

    return app, memory

# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import StateGraph, MessagesState
# from langgraph.prebuilt import create_react_agent
# from langchain_core.messages import AIMessage
# from langchain_core.tools import Tool
# from langchain_deepseek import ChatDeepSeek
# from dotenv import load_dotenv
# from langchain_google_community import GoogleSearchAPIWrapper


# from .tools import (
#     partselect_search, add_to_cart, view_cart, checkout,
#     add_shipping_address, track_order, return_policy,
#     cancel_order, help_links
# )

# load_dotenv()

# search = GoogleSearchAPIWrapper()
# # Tool Definitions
# tools = [

#     Tool(
#         name="PartSelectSearch",
#         func=lambda q: search.run(f"site:partselect.com {q}"),
#         description=(
#             "Search ONLY for Refrigerator or Dishwasher parts from partselect.com. "
#             "Use specific part names, symptoms (e.g., ice maker broken), or model numbers. "
#             "Never respond for microwaves, ovens, or any other category."
#         )
#     ),
#     # Tool(
#     #     name="PartSelectSearch",
#     #     func=partselect_search,
#     #     description=(
#     #         "Search for appliance parts on PartSelect.com using PS part numbers (e.g., PS123456) or model numbers."
#     #     )
#     # ),
#     Tool(
#         name="AddToCart",
#         func=add_to_cart,
#         description="Add a part to the cart. Requires: part_number"
#     ),
#     Tool(
#         name="ViewCart",
#         func=view_cart,
#         description="View current cart contents."
#     ),
#     Tool(
#         name="Checkout",
#         func=checkout,
#         description="Checkout and create an order from cart contents."
#     ),
#     Tool(
#         name="AddShippingAddress",
#         func=add_shipping_address,
#         description="Attach a shipping address to the order. Requires: address"
#     ),
#     Tool(
#         name="TrackOrder",
#         func=track_order,
#         description="Check the status of your current order."
#     ),
#     Tool(
#         name="ReturnPolicy",
#         func=return_policy,
#         description="Show return policy. Optional input: part_number"
#     ),
#     Tool(
#         name="CancelOrder",
#         func=cancel_order,
#         description="Cancel the current order."
#     ),
#     Tool(
#         name="HelpLinks",
#         func=help_links,
#         description="Access FAQs, installation help, and official resources."
#     ),
# ]

# #  Agent Instructions
# system_instructions = """
# You are a helpful assistant for PartSelect.com that helps users find and order refrigerator or dishwasher parts.

# Use tools whenever possible. Your key responsibilities:

# 1. 🔍 **Search Parts**
#    - For PS numbers or model numbers, always start with PartSelectSearch.
#    - If part is found, provide name, price, and a clickable link in this format:
#      **PS123456** (Part Name) $19.99  
#      <a href="URL" target="_blank">View Part</a>
#    - Ask: “Would you like to add this to your cart?”

# 2. 🛒 **Handle Cart & Orders**
#    - Use AddToCart to add items.
#    - Use ViewCart to list items.
#    - Use Checkout to create an order.
#    - Use AddShippingAddress to capture delivery info.
#    - Use TrackOrder and CancelOrder for post-purchase support.

# 3. ❓ **Support & Help**
#    - Offer return_policy, HelpLinks for troubleshooting or installation help.

# 🔧 Format:
# - Use emoji sections (e.g., 📦, 🛠️, 🔧) for clarity.
# - Keep technical explanations simple and customer-friendly.
# - Maximum 3 recommended parts per answer.

# Avoid suggesting any non-PartSelect products unless explicitly requested.
# """

# def build_agent_for_session(session_id: str, callback_handler=None):
#     print(f"[build_agent_for_session] Creating agent components for session: {session_id}")
#     memory = MemorySaver() # In-memory checkpointer for this session

#     # LLM Setup
#     base_model = ChatDeepSeek(
#         model="deepseek-chat",
#         temperature=0.2,
#         streaming=True, 
#         max_tokens=None, 
#         timeout=None,
#         max_retries=2,
#     )

#     agent_runnable = create_react_agent(base_model, tools, prompt=system_instructions) # Pass instructions here
#     workflow = StateGraph(MessagesState)
#     workflow.add_node("agent", agent_runnable)

#     workflow.set_entry_point("agent")

#     def should_continue(state: MessagesState):
#         messages = state['messages']
#         last_message = messages[-1]

#         if hasattr(last_message, "tool_calls") and last_message.tool_calls:
#             return "agent" # Back to the agent node to execute the tool
        
#         if isinstance(last_message, AIMessage):
#              return "__end__"
        
#         return "agent"


#     workflow.add_conditional_edges(
#         "agent", 
#         should_continue,
#         {
#             "agent": "agent",
#             "__end__": "__end__" 
#         }
#     )


#     app = workflow.compile(checkpointer=memory)
#     print(f"[build_agent_for_session] Compiled graph app for session: {session_id}")

  
#     return app, memory
