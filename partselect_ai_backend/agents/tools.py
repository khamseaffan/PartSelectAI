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

# --- Google Search Wrapper (Used as fallback) ---
search = GoogleSearchAPIWrapper()

# --- Keyword Search Tool (Fallback) ---
def search_partselect_keywords(query: str) -> str:
    """Search partselect.com using general keywords, symptoms, or part/model numbers."""
    print(f"[Tool] Executing Keyword Search for: {query}")
    try:
        # Add appliance context to potentially improve results
        search_query = f"site:partselect.com Refrigerator OR Dishwasher {query}"
        results = search.run(search_query)
        if not results or "No good Google Search Result was found" in results:
            return f"❌ No results found on PartSelect for '{query}' using keyword search."
        return f"Keyword search results for '{query}' (summarize relevant parts):\n{results}" # Limit result length
    except Exception as e:
        print(f"Error during keyword search: {e}")
        return f"⚠️ An error occurred during keyword search: {str(e)}"

def add_to_cart(tool_input: dict, **kwargs) -> str:
    """
    Adds or updates a specific part in the shopping cart.
    Requires MANDATORY arguments in dictionary: 'part_number', 'quantity', 'name'.
    """
    session_id = kwargs.get("config", {}).get("configurable", {}).get("thread_id")
    if not session_id: return "❌ Tool Error: Session ID missing."

    if '__arg1' in tool_input and isinstance(tool_input['__arg1'], str):
        try: tool_input = json.loads(tool_input['__arg1'])
        except json.JSONDecodeError: return f"❌ Tool Error: Invalid JSON in __arg1."
    elif not isinstance(tool_input, dict): return f"❌ Tool Error: Expected dictionary input."

    if 'part_number' not in tool_input: return "❌ Tool Input Error: 'part_number' missing."
    if 'quantity' not in tool_input: return "❌ Tool Input Error: 'quantity' missing."
    if 'name' not in tool_input: return "❌ Tool Input Error: 'name' missing."

    part_number = tool_input['part_number']
    quantity_raw = tool_input['quantity']
    name = tool_input['name']

    if not isinstance(part_number, str): return f"❌ Tool Input Error: 'part_number' must be string."
    if not isinstance(name, str): return f"❌ Tool Input Error: 'name' must be string."

    try:
        quantity = int(quantity_raw)
        if quantity <= 0: return f"❌ Tool Input Error: 'quantity' must be positive."
    except (ValueError, TypeError): return f"❌ Tool Input Error: 'quantity' must be whole number."

    pn_formatted = part_number.strip().upper()
    if not re.match(r'^PS\d+$', pn_formatted):
        return f"❌ Invalid Format: 'part_number' needs PS format (e.g., PS123456)."

    try:
        success = redis_manager.add_to_cart(session_id, pn_formatted, quantity, name)
        if success:
            name_str = f" ({name})" if name else ""
            return f"✅ Added/Updated {quantity}x **{pn_formatted}**{name_str} to your cart."
        else:
            return f"⚠️ Could not add/update {pn_formatted}. Storage operation failed."
    except Exception as e:
        print(f"Error during Redis call in AddToCart tool: {e}")
        return f"❌ Error storing item in cart."


def view_cart(tool_input: dict, **kwargs) -> str:
    """Views the current contents (part number, quantity, name) of the shopping cart."""
    session_id = kwargs.get("config", {}).get("configurable", {}).get("thread_id")
    if not session_id: return "❌ Tool Error: Session ID is missing."

    try:
        cart_items_dict = redis_manager.get_cart(session_id) # Returns Dict[str, Dict[str, Any]]
        if not cart_items_dict: return "🛒 Your cart is currently empty."

        items_formatted_lines = []
        for part_num, details in cart_items_dict.items():
            qty = details.get("quantity", 0)
            name = details.get("name", "")
            name_str = f" ({name})" if name else ""
            items_formatted_lines.append(f"- {qty}x **{part_num}**{name_str}")

        if not items_formatted_lines: return "🛒 Cart empty or contains invalid data."

        items_formatted = "\n".join(items_formatted_lines)
        return f"📦 Cart Contents:\n{items_formatted}\n(Note: Prices/totals not shown.)"
    except Exception as e:
        print(f"Error in ViewCart tool: {e}")
        return "❌ Error retrieving cart contents."


def checkout(tool_input: dict, **kwargs) -> str:
    """Finalizes the cart details for this session and directs user to PartSelect.com."""
    session_id = kwargs.get("config", {}).get("configurable", {}).get("thread_id")
    if not session_id: return "❌ Tool Error: Session ID is missing."

    try:
        cart_items_dict = redis_manager.get_cart(session_id)
        if not cart_items_dict: return "🛒 Your cart is empty. Please add items before checking out."

        # Create a record of the finalized cart state
        order_id = f"REC-{uuid.uuid4().hex[:6].upper()}" # Simple session record ID
        order_data = {
            "order_id": order_id,
            "items": cart_items_dict, # The final state of the cart
            "created_at": datetime.now().isoformat()
            # Status implicitly 'finalized' by being in the order record
        }
        order_recorded = redis_manager.create_order(session_id, order_data)

        if order_recorded:
            # Clear the active cart after finalizing it
            cart_cleared = redis_manager.clear_cart(session_id)
            if not cart_cleared:
                 print(f"[Checkout Warning] Failed to clear active cart for session {session_id} after checkout.")

            # Prepare message for user
            items_count = sum(details.get("quantity", 0) for details in cart_items_dict.values())
            part_plural = "item" if items_count == 1 else "items"
            partselect_homepage = "https://www.partselect.com/"

            return (
                f"✅ Okay, your cart containing {items_count} {part_plural} is ready for purchase.\n"
                f"To complete your order securely, please go to the official PartSelect website, add the item(s) to your cart *there*, and proceed through their checkout process:\n"
                f"<a href='{partselect_homepage}' target='_blank'>Go to PartSelect.com</a>\n"
                f"(A record of this session's cart (ID: {order_id}) has been noted.)" # Minimal mention of record
            )
        else:
            return "❌ There was an issue finalizing the cart record. Please try again."
    except Exception as e:
        import traceback # Keep for debugging checkout issues
        print(f"Error in Checkout tool for session {session_id}: {type(e).__name__} - {e}")
        print(traceback.format_exc())
        return "❌ An unexpected error occurred during checkout preparation."




def return_policy(tool_input: dict, **kwargs) -> str:
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

# Using the improved version of help_links from previous discussion
def help_links(tool_input: dict, **kwargs) -> str:
    """Provide helpful links: General FAQs, main category pages, and repair help."""
    # Returns static formatted links
    return (
        "🛠️ Helpful Links:\n"
        "- <a href='https://www.partselect.com/Refrigerator-Parts.htm' target='_blank'>Refrigerator Parts Catalog</a>\n"
        "- <a href='https://www.partselect.com/Dishwasher-Parts.htm' target='_blank'>Dishwasher Parts Catalog</a>\n"
        "- <a href='https://www.partselect.com/Repair/Refrigerator/' target='_blank'>Refrigerator Repair Help</a>\n"
        "- <a href='https://www.partselect.com/Repair/Dishwasher/' target='_blank'>Dishwasher Repair Help</a>\n"
        "- <a href='https://www.partselect.com/Repair.aspx' target='_blank'>General Installation Guides & FAQs</a>"
    )
# # --- Robust Parsers (Adapted from your original scraping code) ---
# def _parse_part_page(url: str, html_content: str) -> Optional[Dict]:
#     """Parses HTML content from a PartSelect part page."""
#     try:
#         soup = BeautifulSoup(html_content, 'html.parser')
#         part_number_el = soup.find('span', {'itemprop': 'sku'})
#         name_el = soup.find('h1', {'itemprop': 'name'})
#         price_el = soup.find('meta', {'itemprop': 'price'})

#         if not all([part_number_el, name_el, price_el]):
#             print(f"Warning: Missing essential elements on part page: {url}")
#             return None # Indicate parsing failure

#         part_number = part_number_el.text.strip()
#         name = name_el.text.strip()
#         price = price_el['content']

#         compatible_models = []
#         try:
#             comp_list = soup.select('.js-part-compatibility-list li') # Example selector - **VERIFY THIS SELECTOR**
#             if comp_list:
#                 compatible_models = [li.text.strip() for li in comp_list[:5]] # Limit results
#         except Exception as e:
#             print(f"Warning: Could not parse compatibility list from {url}: {e}")

#         description = "Not Available"
#         try:
#             desc_el = soup.find('div', {'itemprop': 'description'})
#             if desc_el:
#                 description = desc_el.text.strip()[:300] + '...' # Limit length
#         except Exception as e:
#             print(f"Warning: Could not parse description from {url}: {e}")


#         return {
#             'part_number': part_number,
#             'name': name,
#             'price': price,
#             'compatible_models': compatible_models,
#             'description': description,
#             'url': url
#         }
#     except Exception as e:
#         print(f"Error parsing part page {url}: {type(e).__name__} - {e}")
#         return None

# def _parse_model_page(url: str, html_content: str) -> Optional[Dict]:
#     """Parses HTML content from a PartSelect model page."""
#     try:
#         soup = BeautifulSoup(html_content, 'html.parser')
#         related_parts = []
#         # **VERIFY SELECTORS BELOW - Inspect PartSelect's model page HTML**
#         part_items = soup.select('.diagram-parts-list .list-group-item') # Example selector
#         if part_items:
#             for div in part_items[:5]: # Limit results
#                 try:
#                     part_link_el = div.select_one('.js-part-link') # Example selector
#                     part_name_el = div.select_one('.info .title') # Example selector
#                     price_el = div.select_one('.price .js-part-price') # Example selector

#                     if part_link_el and 'href' in part_link_el.attrs and part_name_el:
#                         part_number = part_link_el.text.strip() # Assuming text is PS number
#                         part_url = part_link_el['href']
#                         # Ensure URL is absolute
#                         if part_url.startswith('/'):
#                             part_url = f"https://www.partselect.com{part_url}"

#                         related_parts.append({
#                             'part_number': part_number,
#                             'url': part_url,
#                             'name': part_name_el.text.strip(),
#                             'price': price_el.text.strip() if price_el else 'N/A'
#                         })
#                 except Exception as item_e:
#                      print(f"Warning: Skipping a part item on model page {url} due to parsing error: {item_e}")


#         symptoms = []
#         try:
#             # **VERIFY SELECTOR - Inspect HTML for symptoms section**
#             symptom_list = soup.select('#js-symptoms-section .list-group-item a') # Example selector
#             if symptom_list:
#                 symptoms = [li.text.strip() for li in symptom_list[:5]] # Limit results
#         except Exception as e:
#             print(f"Warning: Could not parse symptoms list from {url}: {e}")

#         model_number_el = soup.find('h1', {'itemprop': 'name'}) # Often model number is in H1
#         model_number = model_number_el.text.strip().replace("Parts for ", "") if model_number_el else url.split('/')[-2]


#         # Only return if we found *something* potentially useful
#         if not related_parts and not symptoms:
#              print(f"Warning: No relevant parts or symptoms parsed from model page: {url}")
#              # Returning basic info anyway might be useful if page exists
#              # return None

#         return {
#             'model_number': model_number,
#             'related_parts': related_parts,
#             'symptoms': symptoms,
#             'url': url
#         }
#     except Exception as e:
#         print(f"Error parsing model page {url}: {type(e).__name__} - {e}")
#         return None

# # --- Specific Part Number Tool (Direct URL Guess + Fallback) ---
# def _attempt_direct_part_url(part_number: str) -> Optional[str]:
#     """Tries accessing the part page via direct URL guess and parses if successful."""
#     pn = part_number.strip().upper()
#     if not re.match(r'^PS\d+$', pn):
#         print(f"[Tool] Invalid PS number format for direct URL: {part_number}")
#         return None # Invalid format

#     # Common URL pattern - adjust if PartSelect changes this
#     base_url = f"https://www.partselect.com/{pn}-"
#     print(f"[Tool] Attempting Direct URL for Part: {base_url}")
#     final_url_to_parse = None
#     html_content = None

#     try:
#         response = requests.get(base_url, allow_redirects=False, timeout=7)
#         print(f"[Tool] Direct URL guess ({base_url}) status: {response.status_code}")

#         if 300 <= response.status_code < 400 and 'Location' in response.headers:
#             location = response.headers['Location']
#             # Basic check if redirect URL looks like a plausible part page
#             if f"/{pn}" in location or "/PartDetail" in location or "?PartID=" in location:
#                 print(f"[Tool] Redirected to: {location}")
#                 final_url_to_parse = location
#             else:
#                  print(f"[Tool] Redirect location doesn't look like part page: {location}")
#                  return None # Unlikely to be the correct page

#         elif response.status_code == 200:
#              print(f"[Tool] Direct URL {base_url} worked (200 OK).")
#              final_url_to_parse = base_url # Parse the current page
#              html_content = response.text

#         else:
#              print(f"[Tool] Direct URL attempt failed or was not a part page.")
#              return None # Failed

#         # If we have a potential URL, fetch its content (if not already fetched)
#         if final_url_to_parse and not html_content:
#              content_response = requests.get(final_url_to_parse, timeout=10)
#              content_response.raise_for_status()
#              html_content = content_response.text

#         # Parse the content
#         if final_url_to_parse and html_content:
#              parsed_data = _parse_part_page(final_url_to_parse, html_content)
#              if parsed_data:
#                  # Format the structured data nicely for the LLM
#                  compat_str = ', '.join(parsed_data.get('compatible_models', [])) or 'Not Available'
#                  return (
#                      f"✅ Found part via direct URL:\n"
#                      f"**{parsed_data['part_number']}** ({parsed_data['name']}) ${parsed_data['price']}\n"
#                      f"<a href='{parsed_data['url']}' target='_blank'>View Part Details</a>\n"
#                      f"Description: {parsed_data.get('description', 'N/A')}\n"
#                      f"Compatible with (sample): {compat_str}"
#                  )
#              else:
#                  print(f"[Tool] Failed to parse content from {final_url_to_parse}")
#                  # Return indication of existence but parsing failure? Or just fail?
#                  # return f"⚠️ Found a page for {pn} at {final_url_to_parse} but could not parse details."
#                  return None # Treat as failure if parsing doesn't work

#     except requests.exceptions.Timeout:
#          print(f"[Tool] Timeout during direct URL attempt for part: {part_number}")
#          return None
#     except requests.exceptions.RequestException as e:
#         print(f"[Tool] Request error during direct URL attempt for part {part_number}: {e}")
#         return None
#     except Exception as e:
#         print(f"[Tool] Unexpected error during direct part URL attempt {part_number}: {e}")
#         return None

#     return None # Explicitly return None if no success path was hit


# def find_part_page_by_number(part_number: str) -> str:
#     """Use this FIRST to find a specific part page using its PS number (e.g., PS123456). Falls back to keyword search if direct lookup fails."""
#     print(f"[Tool] Trying FindPartPageByNumber for: {part_number}")
#     direct_result = _attempt_direct_part_url(part_number)
#     if direct_result:
#         return direct_result
#     else:
#         print(f"[Tool] Direct URL lookup failed for {part_number}. Falling back to keyword search.")
#         # Fallback to keyword search
#         return search_partselect_keywords(part_number)

# # --- Specific Model Number Tool (Direct URL Guess + Fallback) ---
# def _attempt_direct_model_url(model_number: str) -> Optional[str]:
#     """Tries accessing the model page via direct URL guess and parses if successful."""
#     mn = model_number.strip()
#     if not mn: return None

#     # Common URL pattern - adjust if PartSelect changes this
#     model_url = f"https://www.partselect.com/Models/{quote_plus(mn)}/"
#     print(f"[Tool] Attempting Direct URL for Model: {model_url}")
#     try:
#         response = requests.get(model_url, timeout=10)
#         print(f"[Tool] Direct URL guess ({model_url}) status: {response.status_code}")
#         response.raise_for_status() # Raise error for bad status codes (4xx, 5xx)

#         if response.status_code == 200:
#             print(f"[Tool] Direct model URL successful.")
#             parsed_data = _parse_model_page(model_url, response.text)
#             if parsed_data:
#                 # Format nicely for LLM
#                 part_list_str = "\n".join([f"- {p['part_number']} ({p['name']}) ${p.get('price', 'N/A')}" for p in parsed_data.get('related_parts', [])]) or "No specific parts listed."
#                 symptom_list_str = "\n".join([f"- {s}" for s in parsed_data.get('symptoms', [])]) or "No common symptoms listed."
#                 return (
#                     f"✅ Found model page via direct URL:\n"
#                     f"**Model:** {parsed_data['model_number']}\n"
#                     f"<a href='{parsed_data['url']}' target='_blank'>View Full Model Details & Diagrams</a>\n\n"
#                     f"**Common Parts (Sample):**\n{part_list_str}\n\n"
#                     f"**Common Symptoms:**\n{symptom_list_str}"
#                 )
#             else:
#                 print(f"[Tool] Direct model URL worked, but failed to parse details from {model_url}")
#                 # Return basic success message if parsing failed but page exists
#                 return f"✅ Found model page via direct URL: <a href='{model_url}' target='_blank'>View Model Details</a> (Could not automatically extract parts/symptoms)."
#         else:
#             # This case might not be hit due to raise_for_status, but included for clarity
#             print(f"[Tool] Direct model URL attempt returned unexpected status: {response.status_code}")
#             return None

#     except requests.exceptions.Timeout:
#          print(f"[Tool] Timeout during direct URL attempt for model: {model_number}")
#          return None
#     except requests.exceptions.RequestException as e:
#         # Handle 404 specifically as "not found", other errors as general failures
#         if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
#              print(f"[Tool] Direct model URL not found (404): {model_url}")
#         else:
#              print(f"[Tool] Request error during direct URL attempt for model {model_number}: {e}")
#         return None # Failed
#     except Exception as e:
#         print(f"[Tool] Unexpected error during direct model URL attempt {model_number}: {e}")
#         return None
