import uuid
import re
import json
import requests
import os
from redis import Redis
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from langchain_core.tools import Tool
from dotenv import load_dotenv
from datetime import datetime
from redis_manager import redis_manager
from langchain_google_community import GoogleSearchAPIWrapper # Ensure this is imported
from typing import Optional, Dict, List # Import Optional

load_dotenv()

search = GoogleSearchAPIWrapper()


def search_partselect_keywords(query: str) -> str:
    print(f"[Tool] Executing Keyword Search for: {query}")
    try:
        search_query = f"site:partselect.com {query}"
        results = search.run(search_query)
        if not results or "No good Google Search Result was found" in results:
            return f"❌ No results found on PartSelect for '{query}' using keyword search."
        return f"Keyword search results for '{query}' (summarize relevant parts):\n{results}" # Limit result length
    except Exception as e:
        print(f"Error during keyword seßarch: {e}")
        return f"⚠️ An error occurred during keyword search: {str(e)}"


def add_to_cart(tool_input: dict) -> str:
    """
    Simplified: Adds or updates a part in the shopping cart.
    Expects 'session_id', 'part_number', 'quantity', and 'name' directly in tool_input.
    """
    print(f"Working add to cart:\n{tool_input}")
    session_id = tool_input.get("session_id")
    part_number = tool_input.get("part_number")
    quantity = tool_input.get("quantity")
    name = tool_input.get("name")

    # Basic field checks
    if not session_id:
        print("❌ Error: 'session_id' missing from tool_input.")
        return "❌ Error: 'session_id' missing from tool_input."
    if not part_number:
        print("❌ Error: 'part_number' missing.")
        return "❌ Error: 'part_number' missing."
    if not quantity:
        print("❌ Error: 'quantity' missing.")
        return "❌ Error: 'quantity' missing."
    if not name:
        print("❌ Error: 'name' missing.")
        return "❌ Error: 'name' missing."

    
    # Attempt to add to Redis cart
    try:
        success = redis_manager.add_to_cart(session_id, part_number, quantity, name)
        if success:
            return f"✅ Added/Updated {quantity}x **{part_number}** ({name}) to your cart."
        else:
            return f"⚠️ Could not add/update {part_number}. Storage operation failed."
    except Exception as e:
        print(f"Error in add_to_cart: {e}")
        return "❌ Unexpected error storing item in cart."


def view_cart(tool_input: dict,  **kwargs) -> str:
    """
    Simplified: Views the current cart contents.
    Expects 'session_id' in tool_input.
    """
    session_id = tool_input.get("session_id")
    if not session_id:
        return "❌ Error: 'session_id' missing from tool_input."

    try:
        cart_items_dict = redis_manager.get_cart(session_id)
        if not cart_items_dict:
            return "🛒 Your cart is currently empty."

        lines = []
        for part_num, details in cart_items_dict.items():
            qty = details.get("quantity", 0)
            name = details.get("name", "")
            name_str = f" ({name})" if name else ""
            lines.append(f"- {qty}x **{part_num}**{name_str}")

        if not lines:
            return "🛒 Your cart is empty or has invalid data."

        return "📦 Cart Contents:\n" + "\n".join(lines) + "\n(Prices/totals not shown.)"
    except Exception as e:
        print(f"Error in view_cart: {e}")
        return "❌ Error retrieving cart contents."


def checkout(tool_input: dict) -> str:
    """
    Simplified: Finalizes the cart for this session and directs user to PartSelect.com.
    Expects 'session_id' in tool_input.
    """
    session_id = tool_input.get("session_id")
    if not session_id:
        return "❌ Error: 'session_id' missing from tool_input."

    try:
        cart_items_dict = redis_manager.get_cart(session_id)
        if not cart_items_dict:
            return "🛒 Your cart is empty. Please add items before checking out."

        # Create an order record
        order_id = f"REC-{uuid.uuid4().hex[:6].upper()}"
        order_data = {
            "order_id": order_id,
            "items": cart_items_dict,
            "created_at": datetime.now().isoformat()
        }
        success = redis_manager.create_order(session_id, order_data)
        if not success:
            return "❌ Error finalizing the order. Please try again."

        # Clear the cart after finalizing
        redis_manager.clear_cart(session_id)

        items_count = sum(item.get("quantity", 0) for item in cart_items_dict.values())
        plural = "item" if items_count == 1 else "items"

        return (
            f"✅ Your cart with {items_count} {plural} is ready to purchase.\n"
            f"To complete your order, please visit PartSelect.com, add the item(s) again, and checkout there:\n"
            f"<a href='https://www.partselect.com' target='_blank'>Go to PartSelect.com</a>\n"
            f"(Order record {order_id} has been noted.)"
        )
    except Exception as e:
        print(f"Error in checkout: {e}")
        return "❌ An unexpected error occurred during checkout."





def return_policy(tool_input: dict) -> str:
    """Provide information about PartSelect's return policy."""
    part_number = tool_input.get("part_number") # Optional input
    # Basic policy text - **VERIFY ACTUAL POLICY ON PARTSELECT.COM**
    policy_text = (
        "PartSelect offers a 30-day return policy on most parts. "
        "Parts must be unused, in their original packaging, and in resalable condition. "
        "Installed or damaged parts are generally not eligible for return. "
        "Please visit the Returns section on PartSelect.com for full details and to initiate a return."
    )
    if part_number:
        return f"✅ Regarding part **{part_number}**: {policy_text}"
    else:
        return f"✅ General Return Policy: {policy_text}"

def help_links(tool_input: dict) -> str:
    """Provide helpful links: General FAQs, main category pages, and repair help."""
    return (
        "🛠️ Helpful Links:\n"
        "- <a href='https://www.partselect.com/Refrigerator-Parts.htm' target='_blank'>Refrigerator Parts Catalog</a>\n"
        "- <a href='https://www.partselect.com/Dishwasher-Parts.htm' target='_blank'>Dishwasher Parts Catalog</a>\n"
        "- <a href='https://www.partselect.com/Repair/Refrigerator/' target='_blank'>Refrigerator Repair Help</a>\n"
        "- <a href='https://www.partselect.com/Repair/Dishwasher/' target='_blank'>Dishwasher Repair Help</a>\n"
        "- <a href='https://www.partselect.com/Repair.aspx' target='_blank'>General Installation Guides & FAQs</a>"
    )